# Coding Layer for HiveBot

This layer adds full‑stack web development capabilities to HiveBot. It includes:

- **Roles:** Frontend Developer, Backend Developer, DevOps Engineer, Database Administrator
- **Skills:** HTML, CSS, JavaScript, React, REST API, database schema, SQL, authentication, Dockerfile, GitHub Actions, deploy script
- **Custom Loop Handler:** Implements a build‑test‑review‑fix cycle
- **Lifecycle:** draft → built → tested → reviewed → final (with failed state)
- **Planner Templates:** Few‑shot examples for common goals
- **Training Tasks:** Example tasks and evaluators for self‑improvement
- **Configuration:** GitHub token, default tech stack, etc.

## Installation

1. Ensure HiveBot is running and you have admin access.
2. Install the layer via the UI or CLI:

   ```bash
   hivebot layer install https://github.com/rayccio/layer-coding.git
   ```

3. Enable the layer:

   ```bash
   hivebot layer enable coding
   ```

4. Configure the layer (optional) – provide GitHub token, default stack, etc.

## Usage

After installation, new roles become available in the agent creation dropdown. Skills from this layer can be installed on agents. Create a goal like "Build a responsive landing page with React" and the layer will decompose it into tasks using its custom planner and loop handler.

## Training

The layer includes example training tasks in the `training/` directory. The meta‑agent can use these to evaluate and improve bots. Evaluators are defined in `evaluators.py`.

## Development & Testing

To run tests locally:

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

The tests are also run automatically in GitHub Actions on every push and pull request.

## Files

- `manifest.json` – layer metadata
- `roles/` – role definitions
- `skills/` – skill implementations (Python code)
- `planner/` – custom planner and templates
- `loop.py` – custom loop handler
- `lifecycle.json` – artifact state machine
- `config/settings.json` – configuration schema
- `training/` – training tasks and evaluators
- `tests/` – unit tests
- `README.md` – this file

## Contributing

Feel free to add more skills or improve existing ones. Pull requests welcome!

---

*Maintained by the HiveBot team.*
