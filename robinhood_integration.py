import aiohttp
import os
from typing import Optional, Dict, Any

from utils.errors import IntegrationAuthError, IntegrationAPIError
from models.integration import Integration

year = "2023"


class RobinhoodIntegration(Integration):
    def __init__(self, authorization_token: str):
        super().__init__("robinhood")
        self.authorization_token = authorization_token

    async def _handle_response(
        self, response: aiohttp.ClientResponse
    ) -> Dict[str, Any]:
        if response.status == 200:
            return response
        elif response.status == 401:
            raise IntegrationAuthError("Invalid or expired token", response.status)
        else:
            raise IntegrationAPIError(
                self.integration_name, f"HTTP error occurred: {response.status}"
            )

    async def get_tax_documents(self):
        api_url = "https://bonfire.robinhood.com/tax_center_web/"
        headers = {"authorization": f"Bearer {self.authorization_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers) as response:
                response_data = await self._handle_response(response)
                data = await response_data.json()
        print(data)

        downloaded_files = []

        tax_rows = self.safe_get(
            data, ["content", "tax_rows", year], "get_tax_documents"
        )
        for row in tax_rows:
            content = self.safe_get(row, ["content"], "get_tax_documents")
            for item in content:
                button_action = self.safe_get(
                    item, ["button_action"], "get_tax_documents"
                )
                if button_action:
                    url = self.safe_get(button_action, ["uri"], "get_tax_documents")
                    filename = self.safe_get(
                        item, ["title", "text", "text"], "get_tax_documents"
                    )

                    if filename:
                        file_path = os.path.join("./downloads", filename)

                        async with aiohttp.ClientSession() as session:
                            async with session.get(url, headers=headers) as response:
                                await self._handle_response(response)
                                content = await response.read()
                                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                                with open(file_path, "wb") as f:
                                    f.write(content)
                                downloaded_files.append(file_path)

        return downloaded_files
