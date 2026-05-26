import json
import ssl
import aiohttp
from config import SDP_URL, SDP_API_KEY, SDP_SSL_VERIFY


def _ssl_context():
    if SDP_SSL_VERIFY:
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _headers() -> dict:
    return {
        "authtoken": SDP_API_KEY,
        "Accept": "application/vnd.manageengine.sdp.v3+json",
    }


async def find_requester_id(email: str) -> str | None:
    """Шукає requester за email, повертає внутрішній SDP id або None."""
    url = f"{SDP_URL}/api/v3/requesters"
    search = json.dumps({
        "list_info": {
            "search_criteria": [
                {"field": "email_id", "condition": "is", "value": email}
            ],
            "row_count": 1,
            "start_index": 1,
        }
    })

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers=_headers(),
            params={"input_data": search},
            ssl=_ssl_context(),
        ) as response:
            data = await response.json(content_type=None)

    requesters = data.get("requesters", [])
    if requesters:
        return str(requesters[0]["id"])
    return None


async def get_priorities() -> list[dict]:
    """Повертає список пріоритетів із SDP: [{"id": "...", "name": "..."}, ...]"""
    url = f"{SDP_URL}/api/v3/priorities"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers=_headers(), ssl=_ssl_context()
        ) as response:
            data = await response.json(content_type=None)
    return data.get("priorities", [])


async def create_request(
    requester_id: str, subject: str, description: str, priority: str
) -> dict:
    url = f"{SDP_URL}/api/v3/requests"

    request_data = {
        "request": {
            "subject": subject,
            "description": description,
            "requester": {"id": requester_id},
            "priority": {"name": priority},
        }
    }

    form = aiohttp.FormData()
    form.add_field("input_data", json.dumps(request_data))

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=_headers(), data=form, ssl=_ssl_context()
        ) as response:
            return await response.json(content_type=None)


async def upload_attachment(request_id: str, file_bytes: bytes, filename: str) -> dict:
    url = f"{SDP_URL}/api/v3/requests/{request_id}/attachments"

    form = aiohttp.FormData()
    form.add_field("file", file_bytes, filename=filename, content_type="image/jpeg")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=_headers(), data=form, ssl=_ssl_context()
        ) as response:
            return await response.json(content_type=None)
