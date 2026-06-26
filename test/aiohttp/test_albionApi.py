import unittest

from aioresponses import aioresponses

from albion_assistant.functions.aiohttp import albionApi


class TestAlbionApi(unittest.TestCase):
    async def test_albion_api_successful(self):
        async with aioresponses() as mock_session:
            mock_session.get(
                "https://gameinfo-sgp.albiononline.com/api/gameinfo/players/example_query",
                status=200,
                payload={"example_key": "example_value"},
            )

            result = await albionApi("player", "example_query", "East")

            self.assertEqual(result["Found"], True)
            self.assertEqual(result["example_key"], "example_value")

    async def test_albion_api_404(self):
        async with aioresponses() as mock_session:
            mock_session.get(
                "https://gameinfo-sgp.albiononline.com/api/gameinfo/players/example_query",
                status=404,
                payload={},
            )

            result = await albionApi("player", "example_query", "East")

            self.assertEqual(result["Found"], False)

    async def test_albion_api_error(self):
        async with aioresponses() as mock_session:
            mock_session.get(
                "https://gameinfo-sgp.albiononline.com/api/gameinfo/players/example_query",
                status=500,
                payload={},
            )

            result = await albionApi("player", "example_query", "East")

            self.assertEqual(result["Found"], False)


if __name__ == "__main__":
    unittest.main()
