# MCP Server — same incident tool, hosted for another process to load
"""
---------------------------------------------------------------------------------
Full demo: you classify the ask, then each path uses a different tool style.
---------------------------------------------------------------------------------
1. `Order 8812 arrived damaged. Estimate a refund for 2400 rupees and show the damaged-item policy.`
2. `Courier is stuck. What is the weather in Mumbai right now?`
3. `What is a chargeback, in one sentence?`
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("FAST MCP Server")

import requests
from urllib.request import urlopen

import os
import sys #import sys utility
#import os utility
#load environment variables from the .env file
from dotenv import load_dotenv
load_dotenv()

import logging
# Logs go to stderr — stdout is reserved for the MCP stdio protocol.
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)

# ---------------------------------------------------------------------------
# Placeholder API key for the weather provider (e.g. OpenWeatherMap).
# Fill this in or export WEATHER_API_KEY in the environment / .env file.
# ---------------------------------------------------------------------------
WEATHER_API_KEY: str | None = os.environ["WEATHER_API_KEY"]  # TODO: placeholder - put your weather API key here

@mcp.tool()
def fetch_refund_policy(status:str) -> int:
    """
    Fetch the overall refund policy applied in various cases, depending on the order status. 
    This method defines the total percentage refund depending on the order status
    """
    logging.info("Calling Refund Policy Method ...")
    # Refund Dictinary sopecifying the overall return amount based on the order status
    refund_dict = {
        "damaged":80,
        "shipped":0,
        "pending":0,
        "cancelled":100,
    }

    # For the undefined and unknown status, immediate refund is 50%
    return refund_dict.get(status,50)

@mcp.tool()
def refund_amount_calculator(amount:int, refund_percentage:int) -> int:
    """
    This is the refund amount calculator, which is calculated as percentage on the actual amoutn paid
    """
    logging.info("Calling Refund Amount Calculator Method ...")
    # Refund Dictinary sopecifying the overall return amount based on the order status
    import math
    return math.ceil((refund_percentage * amount)/100.0)

@mcp.tool()
def check_order_status(order_id: int) -> dict:
    """
    Check the status of the order using the Order Id passed
    """
    logging.info("Calling Check Order Status Method ...")
    order_status_dict = {
        8812: "Order 8812 is damaged, would be thus refunded",
        8813: "Order 8813 is shipped, please wait for the delivery ",
        8814: "Order 8814 is pending, please wait for the final status update",
        8815: "Order 8815 is cancelled, total amount will be refunded",
    }
    order_status = order_status_dict.get(order_id, "Order status not found, total amount will be refunded")
    return {"order_status": order_status}

@mcp.tool()
def get_live_weather(city: str) -> str:
    """
    Get the current weather conditions (temperature, humidity, sky state, wind) for a given city anywhere in the world.

    Use this tool whenever the user asks about the weather, temperature, forecast or climate conditions in a specific location. The city name
    should be plain text, e.g. 'San Francisco' or 'London'. Requires a valid weather provider API key (WEATHER_API_KEY) to perform the live API call.
    """
    logging.info("Calling Get Live Weather Method ...")
    if not WEATHER_API_KEY:
        return ("Weather lookup unavailable: no API key configured. "
                "Set WEATHER_API_KEY in Prompts/Tools.py or the environment.")

  #  --- Real API call (OpenWeatherMap-style, untested without a key) ---
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    resp = requests.get(url, params={"q": city, "appid": WEATHER_API_KEY, "units": "metric"}, timeout=10)
    data = resp.json()
    if resp.status_code != 200:
        return f"Weather lookup failed for '{city}': {data.get('message', resp.status_code)}"
    main = data["main"]; wind = data["wind"]; sky = data["weather"][0]["description"]
    return (f"Weather in {city}: {sky}, {main['temp']}°C "
            f"(feels like {main['feels_like']}°C), humidity {main['humidity']}%, "
            f"wind {wind.get('speed', 0)} m/s")


if __name__ == "__main__":
    # No prints after mcp.run(): the stdio transport closes stdout on
    # shutdown, so any print there raises "I/O operation on closed file".
    logging.info("Starting mcp server ...")
    mcp.run()