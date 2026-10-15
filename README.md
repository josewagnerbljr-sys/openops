# OpenOps: A Stock-Control Micro-Site Anyone Can Operate

#### Video Demo: <PASTE YOUR YOUTUBE URL HERE>

#### Description:

## 1. What OpenOps is and the problem it solves

Small businesses run on stock: how many units are on the shelf, what just came in, what was sold, what is about to expire. In practice that knowledge lives in spreadsheets, paper notebooks or someone's memory, and the "proper" software that could replace them is either expensive or built for developers. The first version of this project, an open-source business-operations platform, had exactly that flaw: it exposed a REST API. To add ten units of a product you had to obtain a JWT token, craft a JSON body and send an HTTP request. That is fine for a programmer and impossible for the person who actually receives the delivery.

For this final project I kept the engine and replaced the way people use it. OpenOps now ships a **micro-site**: you run one command, `python openops.py serve --open`, and a browser page opens where you can sign in, register products, record stock in and out with one click on the product row, correct a physical count, remove products, manage customers and users, see what is running low or close to expiry, and download CSV reports. No terminal knowledge is needed after the first command, no `pip install` is required (the micro-site uses only Python's standard library), and nothing leaves the computer unless the owner decides to expose it.

The goal was not just "a web page over a database". It is treated as an operations system, so correctness under real conditions mattered more than features: two cashiers selling the last item at the same time must not sell it twice, a removed product must not erase its audit trail, a stranger on the network must not become administrator, and a hostile product name must not execute code in somebody's browser. Most of the design decisions below exist to make those four sentences true, and each one is covered by an automated test.

## 2. How to run it

```bash
git clone https://github.com/josewagnerbljr-sys/openops.git
cd openops
python openops.py init --admin your_username --demo   # creates database, admin and example data
python openops.py serve --open                        # opens http://localhost:8000
```

Requirements: Python 3.10 or newer. `python openops.py --help` lists every command. To run the tests: `pip install -r requirements-dev.txt`, then `python -m pytest test_project.py` from the root and `python -m pytest` from `python/`.

## 3. Project structure: what every file does

**`openops.py`** is the entry point (a CLI router). It does no business work: it parses arguments with `argparse`, merges configuration from flag, environment variable, `openops.config.json` and defaults (in that priority order), validates it (a port such as `abc` produces a friendly message, never a traceback), configures logging and calls the right module. Commands are `init` (database, config file, first administrator, optional demo data), `serve` (starts the micro-site), `expiry` (lists batches close to their expiry date, with `--json` and `--fail-on-found` so a scheduler such as cron can use it), `export` (CSV) and `version`. Heavy imports happen inside each command, so `--help` is instant and never fails because of a business module.

**`test_project.py`** tests that entry point in an isolated temporary folder: invalid ports, broken config files, idempotent `init`, weak passwords, exit codes of `expiry`, CSV header, and the `--db` override.

**`python/openops_core/`** is the technical foundation, free of third-party dependencies. `db.py` wraps SQLite with versioned, namespaced migrations; in this project a re-entrant lock around every statement and a `transaction()` context manager were added (see section 5). `errors.py` defines the exception hierarchy and its HTTP mapping. `config.py` loads layered configuration. `logging.py` writes structured JSON Lines, and now also to a file (`openops.log`), which is the audit trail. `registry.py` registers modules, `events.py` is an in-process event bus, and `roles.py` holds the viewer/operator/admin privilege levels shared by every interface.

**`python/openops_business/`** holds the business domain, one package per module (`products`, `inventory`, `customers`), each with `models.py` (immutable dataclasses that validate themselves), `repository.py` (the only place with SQL), and `service.py` (the facade the rest of the system uses). Inventory depends on products and publishes `stock.changed`, `stock.low` and `stock.expiring_soon` events. This is also where the new product-removal rule lives.

**`python/openops_web/`** is the micro-site. `app.py` is the heart: a `WebApp.handle(method, path, headers, body)` function that returns a response without opening any socket, so routing, permissions and validation are testable in milliseconds. `server.py` is a thin `http.server` adapter that only translates the protocol. `security.py` implements scrypt password hashing, HMAC-signed session tokens and a login throttle. `users.py` stores users and enforces rules such as "the system can never lose its last administrator". `demo.py` seeds example data without touching a database that already has products. `static/index.html`, `static/style.css` and `static/app.js` form the interface: plain HTML, CSS and JavaScript, no framework and no CDN.

**`python/openops_api/`** is the earlier FastAPI REST API. It was kept for integrations that do want an API, and a privilege-escalation bug in it was fixed (section 5), and made it optional. **`go/`** and **`rust/`** contain the earlier command-line health scanner and the AES-256-GCM crypto library of the original monorepo; the micro-site does not need them. **`docs/`** contains the user manual in Portuguese, the submission guide and the video script; `THREAT_MODEL.md` was extended with the micro-site's threats.

## 4. Design choices

**Python's standard library instead of Flask or FastAPI.** A web framework would have been quicker to write, but it would also have required `pip install`, a virtual environment and a working network, which defeats the goal of "anyone can run it". `http.server`, `sqlite3`, `hashlib.scrypt` and `hmac` are enough. The cost is that routing and validation are handled by hand; it is contained by keeping all logic in `app.py`, a pure request-to-response function, and leaving the server as a thin adapter. Because of that separation the 100+ web tests run in a few seconds, and a handful more exercise a real socket.

**A single page with no framework.** The interface is vanilla JavaScript. The most important screen is the product table: every row has a level gauge and a quantity box with "Add" and "Remove" buttons, because the commonest operation (receive or sell N units) should take one click, not a dialog. Rarer operations (batch and expiry date, inventory correction, edit, remove) live behind "More". On phones the row becomes a stacked block so the action buttons stay visible. The interface is in Portuguese and English.

**Stock changes only through movements.** A product's stock is never edited directly; it changes only by an "in", "out" or "adjustment" movement. Creating a product with initial stock records an "Initial stock" movement in the same transaction. The history therefore always explains the number on the screen.

**Removing a product archives it when it has history.** SQLite's foreign key correctly refuses to delete a product that has movements, which originally surfaced as an unhandled server error. A literal delete would destroy the audit trail, so `remove()` deletes products with no history and archives the others (hidden from lists, name released for reuse, movements kept). The interface tells the user which of the two happened.

**Security by default.** Passwords use scrypt with per-user salt; login errors are identical for unknown user and wrong password, and the hash is computed in both cases to avoid a timing leak. Tokens carry only the username and expiry, while the role is read from the database on every request, so demoting or deleting a user takes effect immediately. The first-run setup page only works from the same computer. The server listens on 127.0.0.1 only and validates the `Host` header (DNS rebinding). A Content-Security-Policy forbids inline scripts, the interface uses `textContent` instead of `innerHTML`, CSV exports neutralise spreadsheet formulas, and bodies are capped at 64 KiB.

## 5. Challenges and trade-offs

These problems were found and fixed during development together with the AI assistant (see section 6); the descriptions are how they were diagnosed and solved.

**Concurrency bugs that only appear with real traffic.** A single-threaded test suite passed while the threaded server was wrong. `ThreadingHTTPServer` serves each request in its own thread but all of them share one SQLite connection, and two bugs appeared. First, `Database.query` temporarily sets the connection's `row_factory`; one thread could reset it while another was mid-query, so the second received tuples and crashed with a `TypeError` on `row["id"]`. Second, selling stock was a read-modify-write: two simultaneous sales read the same balance and one overwrote the other, allowing the system to sell items it did not have. The first was fixed with a re-entrant lock around every statement and the second with a lock plus an atomic `transaction()` that stores the movement and the new balance together or not at all. A regression test fires 120 concurrent sales at 50 units of stock and asserts that exactly 50 succeed and the final stock is zero. The trade-off is that writes are serialised inside one process; that is perfectly adequate for a small business and far simpler than a client-server database.

**A privilege-escalation bug in the old API.** `POST /auth/register` accepted a `role` field from anyone, so a visitor could register as `admin`. The fix keeps public registration at `viewer` and requires an administrator's token for anything higher, with regression tests. Those FastAPI tests could not be run in the AI assistant's sandbox (package installation was blocked), so they are verified by the project's continuous-integration workflow rather than there; this is stated openly instead of claiming otherwise.

**Making the business package importable without FastAPI.** The package `__init__` files imported their FastAPI routers, so even the pure domain logic required FastAPI to be installed. The router imports were moved to the API module, which is what allows the micro-site to have zero dependencies, and added a CI job that installs only `pytest` on Python 3.10 and 3.12 to keep that promise honest. Another trade-off is relative versus absolute paths: the database and log are created in the current directory by default, which is visible and simple, and `--db` or the config file override it.

## 6. Authorship, ownership and use of AI assistance

**Owner and author.** OpenOps is created, owned and maintained by **José Wagner Blanco Júnior** (GitHub: [josewagnerbljr-sys](https://github.com/josewagnerbljr-sys)), the sole author and the only person responsible for this submission. Copyright 2024-2026 José Wagner Blanco Júnior. The software is released under the **Apache License 2.0** (`LICENSE`, with the copyright notice in `NOTICE`), which keeps ownership with the author while letting others use, study and modify it.

**What is the author's work.** The earlier OpenOps code (core, business modules, FastAPI API, Go command-line tool and Rust crypto library) was already in this repository before the final-project work began. For this submission the author defined the problem and the requirements (replace the API with a micro-site that anyone can operate without programming knowledge, keep the existing engine, optimise the system as a whole, and meet the CS50 submission rules) and chose the direction.

**What AI did.** CS50's rule for the final project is that AI-based software may be used, that "the essence of the work must still be your own", that AI should amplify and not supplant the student's work, and that its use must be cited in code comments. The use of AI here was **extensive**: Anthropic's Claude (through Claude Code) wrote most of the new implementation of this submission, namely the `openops_web` package, the `openops.py` command line, the fixes to the core and the API, the automated tests, and the first drafts of the documentation, working from the requirements above. It also found and fixed the bugs described in section 5. Every file written or modified that way begins with a comment saying so.

**The author's own contributions in this submission.** [TO BE COMPLETED BY THE AUTHOR BEFORE SUBMITTING, IN HIS OWN WORDS AND ONLY WITH WHAT HE ACTUALLY DID: for example, the features he designed and implemented himself, the parts he rewrote, the decisions he took and why, and what he tested by hand. Delete this bracket afterwards.]

## 7. Testing

`python/openops_web/tests` covers the web layer (permissions per role, input validation, injection attempts, path traversal, throttling, concurrency and a real-socket integration test), `python/openops_core/tests` and `python/openops_business/tests` cover the foundation and domain (including transactions and product archiving), and `test_project.py` covers the command line. The interface was additionally exercised in a real Chromium browser: login, one-click stock entry and exit, product removal, hostile product names rendered as plain text, language switch and a phone-sized viewport.
