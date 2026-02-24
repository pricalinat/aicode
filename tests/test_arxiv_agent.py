import unittest

from multi_agent_system.agents import ArxivAgent
from multi_agent_system.agents.arxiv_agent import ArxivSearchInput
from multi_agent_system.core import Message, Orchestrator


SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2501.00001v1</id>
    <updated>2025-01-01T00:00:00Z</updated>
    <published>2025-01-01T00:00:00Z</published>
    <title> Test Paper Title </title>
    <summary> Test summary content for parsing. </summary>
    <author><name>Alice</name></author>
    <author><name>Bob</name></author>
    <arxiv:primary_category term="cs.CL" />
    <category term="cs.CL" />
    <category term="cs.AI" />
    <link rel="alternate" type="text/html" href="http://arxiv.org/abs/2501.00001v1"/>
    <link title="pdf" rel="related" type="application/pdf" href="http://arxiv.org/pdf/2501.00001v1"/>
  </entry>
</feed>
"""


class ArxivAgentTests(unittest.TestCase):
    def test_build_search_query_with_filters(self) -> None:
        agent = ArxivAgent()
        query = agent._build_search_query(  # noqa: SLF001 - intentional unit test for query builder
            ArxivSearchInput(
                query="large language model",
                category="cs.CL",
                start_year=2023,
                end_year=2025,
            )
        )
        self.assertIn('all:"large language model"', query)
        self.assertIn("cat:cs.CL", query)
        self.assertIn("submittedDate:[202301010000 TO 202512312359]", query)

    def test_handle_parses_feed(self) -> None:
        agent = ArxivAgent()
        agent._query_arxiv = lambda **_: SAMPLE_XML  # noqa: SLF001

        message = Message(task_type="search_arxiv", content={"query": "test"})
        response = agent.handle(message)

        self.assertTrue(response.success)
        self.assertEqual(response.data["count"], 1)
        paper = response.data["papers"][0]
        self.assertEqual(paper["title"], "Test Paper Title")
        self.assertEqual(paper["authors"], ["Alice", "Bob"])
        self.assertEqual(paper["primary_category"], "cs.CL")
        self.assertEqual(paper["pdf_url"], "http://arxiv.org/pdf/2501.00001v1")

    def test_orchestrator_no_agent_found(self) -> None:
        orchestrator = Orchestrator([ArxivAgent()])
        message = Message(task_type="unknown_task", content={})
        response = orchestrator.dispatch(message)

        self.assertFalse(response.success)
        self.assertIn("No agent can handle", response.error or "")


if __name__ == "__main__":
    unittest.main()
