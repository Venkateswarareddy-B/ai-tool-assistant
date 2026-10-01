import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import requests

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq


# --------------------------------------------------
# ENVIRONMENT VARIABLES
# --------------------------------------------------

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# --------------------------------------------------
# FASTAPI
# --------------------------------------------------

app = FastAPI(title="AI Tool Assistant")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": topic,
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": 5,
        "sortBy": "publishedAt",
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

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

llm = ChatGroq(
    model="openai/gpt-oss-120b",
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

    messages = [
        HumanMessage(
            content=request.message
        )
    ]

    # Ask Groq whether a tool is required
    response = llm_with_tools.invoke(
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

        final_response = (
            llm_with_tools.invoke(messages)
        )

        answer = final_response.content

    else:

        answer = response.content

    return {
        "answer": answer,
        "tools_used": used_tools,
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