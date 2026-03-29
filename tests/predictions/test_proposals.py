from __future__ import annotations

from predictions.proposals import list_proposals


class TestProposals:
    def test_returns_list(self):
        proposals = list_proposals()
        assert isinstance(proposals, list)
        assert len(proposals) > 0

    def test_proposal_structure(self):
        proposals = list_proposals()
        for p in proposals:
            assert "name" in p
            assert "description" in p
