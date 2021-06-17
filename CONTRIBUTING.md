# Contribution guide

1. Fork
1. Write some code (with tests if possible)
1. Write some docs
1. Check code formatting.
   In project root folder run `black --check .`
   Proceed in case no issues found. Otherwise run `black .`
1. Run the tests (with your `pipenv shell` activated)
   ```bash
   python -m pytest tests -s
   ```

1. Create a pull request on GitHub
