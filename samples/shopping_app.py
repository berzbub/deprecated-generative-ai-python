# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Shopping assistant sample using Gemini function calling.

This script demonstrates a shopping assistant that searches multiple
shopping platforms for matching items, compares prices, and surfaces
results from trusted stores near the user's location.

Note: Publishing a Python application to the Google Play Store requires
packaging it as an Android app (e.g. via Buildozer/Kivy). The logic
below can be embedded in such a packaged application.
"""

from absl.testing import absltest


class UnitTests(absltest.TestCase):
    def test_shopping_app(self):
        # [START shopping_app]
        import google.generativeai as genai

        # ---------------------------------------------------------------------------
        # Tool definitions – these functions simulate fetching live data from
        # external shopping platforms and a location service.  In a production app
        # you would replace these stubs with real API calls.
        # ---------------------------------------------------------------------------

        def search_products(
            query: str,
            platform: str,
            max_results: int = 5,
        ) -> list[dict]:
            """Search a shopping platform for products matching the query.

            Args:
                query: The product name or description to search for.
                platform: Shopping platform to query, e.g. 'Amazon', 'eBay',
                    'Shopee', 'Lazada', or 'Google Shopping'.
                max_results: Maximum number of results to return.

            Returns:
                A list of product dicts, each with 'name', 'price', 'currency',
                'rating', 'platform', and 'store_id' fields.
            """
            # Simulated results – replace with real API integration.
            simulated_catalog = {
                "Amazon": [
                    {
                        "name": f"{query} – Amazon Basic",
                        "price": 29.99,
                        "currency": "USD",
                        "rating": 4.5,
                        "platform": "Amazon",
                        "store_id": "amz-001",
                    },
                    {
                        "name": f"{query} – Amazon Premium",
                        "price": 49.99,
                        "currency": "USD",
                        "rating": 4.8,
                        "platform": "Amazon",
                        "store_id": "amz-002",
                    },
                ],
                "eBay": [
                    {
                        "name": f"{query} – eBay Listing",
                        "price": 24.50,
                        "currency": "USD",
                        "rating": 4.2,
                        "platform": "eBay",
                        "store_id": "ebay-101",
                    }
                ],
                "Google Shopping": [
                    {
                        "name": f"{query} – Google Shopping Pick",
                        "price": 32.00,
                        "currency": "USD",
                        "rating": 4.6,
                        "platform": "Google Shopping",
                        "store_id": "gshop-201",
                    }
                ],
            }
            results = simulated_catalog.get(platform, [])
            return results[:max_results]

        def get_nearby_stores(
            store_ids: list[str],
            user_location: str,
            radius_km: float = 10.0,
        ) -> list[dict]:
            """Return store details for the given store IDs that are near the user.

            Args:
                store_ids: List of store identifier strings returned by
                    search_products.
                user_location: Human-readable location, e.g. 'Makati City, PH'.
                radius_km: Search radius in kilometres.

            Returns:
                A list of store dicts, each with 'store_id', 'name', 'address',
                'distance_km', and 'trusted' fields.
            """
            # Simulated proximity data – replace with a Maps / geolocation API.
            simulated_stores = {
                "amz-001": {
                    "store_id": "amz-001",
                    "name": "Amazon Fulfillment Center",
                    "address": "123 Commerce St, Metro Area",
                    "distance_km": 2.4,
                    "trusted": True,
                },
                "amz-002": {
                    "store_id": "amz-002",
                    "name": "Amazon Premium Hub",
                    "address": "456 Market Ave, Downtown",
                    "distance_km": 5.1,
                    "trusted": True,
                },
                "ebay-101": {
                    "store_id": "ebay-101",
                    "name": "eBay Local Seller",
                    "address": "789 Trade Blvd, Eastside",
                    "distance_km": 8.3,
                    "trusted": False,
                },
                "gshop-201": {
                    "store_id": "gshop-201",
                    "name": "Google Shopping Partner",
                    "address": "321 Tech Park, Northside",
                    "distance_km": 3.7,
                    "trusted": True,
                },
            }
            nearby = []
            for sid in store_ids:
                store = simulated_stores.get(sid)
                if store and store["distance_km"] <= radius_km:
                    nearby.append(store)
            nearby.sort(key=lambda s: s["distance_km"])
            return nearby

        # ---------------------------------------------------------------------------
        # Build and run the shopping assistant
        # ---------------------------------------------------------------------------

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[search_products, get_nearby_stores],
        )

        chat = model.start_chat(enable_automatic_function_calling=True)

        user_query = (
            "I'm looking for wireless earbuds. "
            "Search Amazon, eBay, and Google Shopping, compare prices, "
            "and tell me which trusted stores near Makati City, PH "
            "offer the best deal within 10 km."
        )

        response = chat.send_message(user_query)
        print(response.text)
        # [END shopping_app]


if __name__ == "__main__":
    absltest.main()
