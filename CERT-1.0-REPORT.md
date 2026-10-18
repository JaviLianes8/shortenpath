# shortenpath 1.0.0 certification report

The 1.0.0 certification bar applied to shortenpath. PyPI has no release of shortenpath
(`https://pypi.org/pypi/shortenpath/json` answered 404 on 2026-10-18), so 1.0.0 is its first
release there and there is no installed base to upgrade from; every change against `main`
(0.2.0, 45b7e87) is still listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (0.2.0, 45b7e87)
- [ ] Baseline gates on 0.2.0
- [ ] API review and 1.0.0 changes (item 1)
- [ ] Errors, typing, docstrings and doctests (items 2 to 5)
- [ ] Ground truth: sources fetched live, reference programs run (item 7)
- [ ] Contract, fuzz and author mutation round (items 6, 9, 18)
- [ ] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [ ] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [ ] Gates (item 15)
- [ ] PR and trace guard CLEAN; the independent reviewer (16), merge and publish (17) and the
      five QA lenses (19) follow
