# SkyRoute Python standards

- Python 3.10 or later, standard library only.
- Put units in names: `_nm`, `_kt`, `_lb`, `_deg`, `_hours`.
- At input boundaries, raise `ValueError` with a message that names the bad value.
- When you answer a question about SkyRoute behavior or policy, end the answer with a line that starts with `Sources:` and lists every file you read for it.
