import logging
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import requests

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq


# --------------------------------------------------
# ENVIRONMENT VARIABLES
# --------------------------------------------------

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

logger = logging.getLogger(__name__)

configured_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]
allowed_origins = configured_origins or [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


# --------------------------------------------------
# FASTAPI
# --------------------------------------------------

app = FastAPI(title="AI Tool Assistant")


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# 1. WEATHER TOOL
# --------------------------------------------------

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    return (
        f"City: {data['name']}\n"
        f"Temperature: {data['main']['temp']}°C\n"
        f"Feels like: {data['main']['feels_like']}°C\n"
        f"Humidity: {data['main']['humidity']}%\n"
        f"Condition: {data['weather'][0]['description']}\n"
        f"Wind: {data['wind']['speed']} m/s"
    )


# --------------------------------------------------
# 2. CURRENCY TOOL
# --------------------------------------------------

@tool
def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> str:
    """Convert using the latest ECB reference rate published by Frankfurter."""

    from_currency = from_currency.strip().upper()
    to_currency = to_currency.strip().upper()

    if not all(
        len(currency) == 3 and currency.isascii() and currency.isalpha()
        for currency in (from_currency, to_currency)
    ):
        return "Currency codes must be three-letter ISO codes, such as USD or INR."

    try:
        amount_decimal = Decimal(str(amount))
    except InvalidOperation:
        return "Enter a valid amount to convert."

    if not amount_decimal.is_finite() or amount_decimal < 0:
        return "The amount must be a finite, non-negative number."

    url = (
        f"https://api.frankfurter.dev/v2/rate/"
        f"{from_currency}/{to_currency}"
    )

    response = requests.get(
        url,
        timeout=10,
    )

    if response.status_code in (404, 422):
        return (
            f"No ECB reference rate is available for "
            f"{from_currency} to {to_currency}."
        )

    response.raise_for_status()

    data = response.json()
    rate = Decimal(str(data["rate"]))
    converted = (amount_decimal * rate).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return (
        f"Conversion: {amount_decimal.normalize():,f} {from_currency} = "
        f"{converted:,.2f} {to_currency}\n"
        f"Rate: 1 {from_currency} = {rate:f} {to_currency}\n"
        f"Rate date: {data['date']}\n"
        "Source: Frankfurter API (ECB reference rate). "
        "Bank and card rates may differ and can include fees."
    )


# --------------------------------------------------
# 3. WIKIPEDIA TOOL
# --------------------------------------------------

@tool
def wikipedia_search(topic: str) -> str:
    """Search Wikipedia for knowledge about a topic."""

    url = (
        "https://en.wikipedia.org/api/rest_v1/"
        f"page/summary/{topic}"
    )

    response = requests.get(
        url,
        timeout=10,
    )

    if response.status_code != 200:
        return "No information found."

    data = response.json()

    return data.get(
        "extract",
        "No summary available.",
    )


# --------------------------------------------------
# 4. CALCULATOR TOOL
# --------------------------------------------------

@tool
def calculator(expression: str) -> str:
    """Calculate a mathematical expression."""

    try:
        allowed = "0123456789+-*/().% "

        if not all(
            char in allowed
            for char in expression
        ):
            return "Invalid mathematical expression."

        result = eval(
            expression,
            {"__builtins__": {}},
            {},
        )

        return f"Result: {result}"

    except Exception:
        return "Invalid mathematical expression."


# --------------------------------------------------
# 5. NEWS TOOL
# --------------------------------------------------

@tool
def get_news(topic: str) -> str:
    """Get recent news about a topic."""

    if not NEWS_API_KEY:
        return "News search is not configured. Set NEWS_API_KEY in the backend environment."

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": topic,
        "language": "en",
        "pageSize": 5,
        "sortBy": "publishedAt",
    }

    headers = {
        "X-Api-Key": NEWS_API_KEY,
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10,
    )

    if response.status_code == 401:
        return (
            "NewsAPI rejected NEWS_API_KEY. Create or activate a valid key, "
            "update the backend environment, and restart the backend."
        )

    if response.status_code == 429:
        return "NewsAPI rate limit or request quota reached. Try again later or check your plan."

    if response.status_code == 403:
        return "NewsAPI denied this request. Check your account plan and endpoint access."

    response.raise_for_status()

    data = response.json()

    articles = data.get(
        "articles",
        [],
    )

    if not articles:
        return "No recent news found."

    result = []

    for article in articles:

        title = article.get(
            "title",
            "No title",
        )

        source = article.get(
            "source",
            {},
        ).get(
            "name",
            "Unknown source",
        )

        result.append(
            f"- {title} ({source})"
        )

    return "\n".join(result)


# --------------------------------------------------
# 6. LOCATION TOOL
# --------------------------------------------------

@tool
def find_location(place: str) -> str:
    """Find latitude and longitude of a place."""

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": place,
        "format": "json",
        "limit": 1,
    }

    headers = {
        "User-Agent": "AI-Tool-Assistant",
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        return "Location not found."

    location = data[0]

    return (
        f"Place: {location['display_name']}\n"
        f"Latitude: {location['lat']}\n"
        f"Longitude: {location['lon']}"
    )


# --------------------------------------------------
# ALL TOOLS
# --------------------------------------------------

tools = [
    get_weather,
    convert_currency,
    wikipedia_search,
    calculator,
    get_news,
    find_location,
]


tool_map = {
    tool.name: tool
    for tool in tools
}


# --------------------------------------------------
# GROQ LLM
# --------------------------------------------------

llm_with_tools = None
if GROQ_API_KEY:
    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=0,
        api_key=GROQ_API_KEY,
    )
    llm_with_tools = llm.bind_tools(tools)


# --------------------------------------------------
# REQUEST MODEL
# --------------------------------------------------

class ChatRequest(BaseModel):
    message: str


# --------------------------------------------------
# CHAT ENDPOINT
# --------------------------------------------------

@app.post("/api/chat")
def chat(request: ChatRequest):

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    if llm_with_tools is None:
        raise HTTPException(
            status_code=503,
            detail="Groq is not configured. Set GROQ_API_KEY in the backend environment.",
        )

    def invoke_groq(messages):
        try:
            return llm_with_tools.invoke(messages)
        except Exception as error:
            logger.exception("Groq request failed")
            raise HTTPException(
                status_code=502,
                detail="Groq request failed. Check GROQ_API_KEY and GROQ_MODEL in the backend environment.",
            ) from error

    messages = [
        HumanMessage(
            content=request.message
        )
    ]

    # Ask Groq whether a tool is required
    response = invoke_groq(
        messages
    )

    used_tools = []

    # --------------------------------------------------
    # EXECUTE TOOL CALLS
    # --------------------------------------------------

    if response.tool_calls:

        messages.append(response)

        for tool_call in response.tool_calls:

            tool_name = tool_call["name"]

            tool_args = tool_call["args"]

            selected_tool = tool_map.get(
                tool_name
            )

            if selected_tool is None:

                tool_result = (
                    "Tool not found."
                )

            else:

                try:

                    tool_result = (
                        selected_tool.invoke(
                            tool_args
                        )
                    )

                except Exception as error:

                    tool_result = (
                        f"Tool error: {str(error)}"
                    )

            used_tools.append({
                "name": tool_name,
                "arguments": tool_args,
                "result": tool_result,
            })

            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                )
            )

        # --------------------------------------------------
        # ASK GROQ FOR FINAL ANSWER
        # --------------------------------------------------

        try:
            summary_messages = [
                SystemMessage(
                    content=(
                        "Summarize the tool results using only facts explicitly "
                        "present in them. Never invent dates, article details, "
                        "claims, calculations, or additional sources. If results "
                        "contain only headlines and source names, say so and list "
                        "only those headlines."
                    )
                ),
                *messages,
            ]
            final_response = llm.invoke(summary_messages)
        except Exception as error:
            logger.exception("Groq summary request failed")
            final_response = None

        content = final_response.content if final_response is not None else ""
        if isinstance(content, list):
            answer = "\n".join(
                part["text"]
                for part in content
                if isinstance(part, dict)
                and isinstance(part.get("text"), str)
            ).strip()
        elif isinstance(content, str):
            answer = content.strip()
        else:
            answer = str(content or "").strip()

        if not answer:
            answer = (
                "The tool finished, but the AI did not return a summary. "
                "See the tool output below."
            )

    else:

        answer = response.content

    return {
        "answer": answer,
        "tools_used": used_tools,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "groq_configured": bool(GROQ_API_KEY),
        "groq_model": GROQ_MODEL if GROQ_API_KEY else None,
    }


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "message": "AI Tool Assistant API is running"
    }


# --------------------------------------------------
# TOOL LIST
# --------------------------------------------------

@app.get("/api/tools")
def get_tools():

    return [
        {
            "name": "get_weather",
            "description": "Get current weather for a city",
        },
        {
            "name": "convert_currency",
            "description": "Convert money between currencies",
        },
        {
            "name": "wikipedia_search",
            "description": "Search Wikipedia",
        },
        {
            "name": "calculator",
            "description": "Calculate mathematical expressions",
        },
        {
            "name": "get_news",
            "description": "Get recent news",
        },
        {
            "name": "find_location",
            "description": "Find latitude and longitude",
        },
    ]