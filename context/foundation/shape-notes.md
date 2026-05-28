---
project: Virtual Parliament — Deploy & Frontend
context_type: brownfield
checkpoint:
  current_phase: 8
  phases_completed: [1, 2, 3, 4, 5, 6, 7]
  frs_drafted: 6
  quality_check_status: accepted
timeline_budget:
  delivery_weeks: null
  hard_deadline: "2026-05-31"
  after_hours_only: true
updated: "2026-05-27"
---

## Current System

Virtual Parliament to multi-agentowa symulacja polskiego Sejmu.

- **Co istnieje:** Python CLI (`parliament "<topic>"`), FastAPI SSE endpoint (`/stream/{session_id}`, `/health`), SQLite schema (sessions, utterances, votes, bill_drafts), 25 Hermes Agent skills (marszałek + 19 ministerstw + 5 partii)
- **Tech stack:** Python 3.11, Hermes Agent 0.14.0, FastAPI, typer, aiosqlite, SQLite, sse-starlette
- **Stan implementacji:** 3 z 5 faz zaimplementowane (foundation, agent skills, orchestrator CLI)
- **Users:** Nikt — projekt nie jest uruchomiony
- **Must preserve:** Hermes skills (marszalek, ministerstwa) muszą działać na serwerze — to core produktu

## Vision & Problem Statement

**Ból:** Projekt istnieje w kodzie, ale nie ma wdrożenia. Bez publicznego URL nie ma demo, nie ma oceny jury, nie ma zgłoszenia konkursowego.

**Driver:** Hermes Agent Challenge — deadline 31 maja 2026. Konkurs wymaga działającej demo + ≤3 min video.

**Zmiana:** Wdrożenie na PaaS (Railway/Fly.io) z publicznym HTTPS URL + Next.js UI streamujące transkrypt przez SSE.

## User & Persona

**Jury Hermes Agent Challenge** — ocenia projekt przez przeglądarkę i/lub demo video. Potrzebuje:
1. Publicznego URL dostępnego z zewnątrz
2. UI, które pokazuje symulację w akcji
3. Działającej demonstracji: wpisz temat → dostań debatę parlamentarną z głosowaniem

## Access Control

Brak logowania — otwarty dostęp przez publiczny URL. Użytkownik (jury) wchodzi na stronę bez rejestracji i natychmiast może użyć aplikacji.

No changes planned for auth model — brak auth w MVP jest celowy (demo konkursowe, nie produkt wieloużytkownikowy).

Klucze API (OPENROUTER_API_KEY, PAGEINDEX_API_KEY) wyłącznie jako env vars na PaaS — nie w repozytorium.

## Success Criteria

### Primary
Użytkownik otwiera publiczny HTTPS URL → wpisuje temat ustawy → widzi live stream debaty parlamentarnej (utterance po utterance przez SSE) → na końcu widzi tabelę głosowania z wynikiem PASSED/REJECTED.

### Secondary
Disclaimer `⚠️ EDUCATIONAL SIMULATION` widoczny na górze i dole strony. Kolory partii w transkrypcie (KO=niebieski, PiS=czerwony itd.).

### Guardrails
- Hermes skills działają na serwerze (Python 3.11 + venv poprawnie skonfigurowane)
- Klucze API nie wyciekają do repozytorium ani logów
- Aplikacja dostępna przed 31 maja 23:59 PDT

Timeline: 4 dni. Zaakceptowane — user potwierdził wykonalność.
Blast radius: Hermes Agent może nie uruchomić się na PaaS (brak Python 3.11/venv) — to krytyczne ryzyko do zaadresowania w pierwszym kroku deploy.

## Functional Requirements

### UI Frontend

- FR-001: Użytkownik może wpisać temat ustawy w formularzu i uruchomić symulację. Priority: must-have. Change: new
  > Socrates: Brak kontrargumentu — bez formularza jury nie może nic zrobić na stronie.

- FR-002: Użytkownik widzi live stream transkryptu debaty (utterance po utterance, SSE) z kolorami per partia. Priority: must-have. Change: new
  > Socrates: Brak kontrargumentu — live stream to jedyna rzecz oddzielająca projekt od statycznego raportu.

- FR-003: Użytkownik widzi tabelę głosowania (5 partii, wynik PASSED/REJECTED) po zakończeniu sesji. Priority: must-have. Change: new
  > Socrates: Brak kontrargumentu — bez tabeli jury nie wie czym zakończyła się sesja.

### Infrastructure

- FR-004: parliament CLI uruchamia się poprawnie na serwerze PaaS (Python 3.11 + Hermes Agent). Priority: must-have. Change: preserved
  > Socrates: Brak kontrargumentu — to fundament, bez którego żaden FR nie zadziała na produkcji.

- FR-005: Projekt posiada konfigurację deploy (Dockerfile lub railway.toml/fly.toml) z env vars dla kluczy API. Priority: must-have. Change: new
  > Socrates: Brak kontrargumentu — infrastruktura konieczna do całości.

- FR-006: FastAPI zawiera nagłówki CORS umożliwiające Next.js (inna domena) wywołanie /stream i /health. Priority: must-have. Change: new
  > Socrates: Brak kontrargumentu — bez CORS przeglądarka zablokuje każdy request z frontendu.

## User Stories

### US-01: Pełna symulacja parlamentarna

**Given** użytkownik otwiera publiczny URL w przeglądarce,
**When** wpisuje temat ustawy i klika "Uruchom",
**Then** widzi live stream utterance'ów debaty pojawiających się jeden po drugim z kolorami partii, a po zakończeniu tabelę głosowania z wynikiem PASSED lub REJECTED.

## Business Logic

No domain logic change. To zmiana infrastrukturalna/prezentacyjna.

Istniejąca reguła domenowa (niezmieniona): system przyjmuje temat ustawy → Marszałek orchestruje konsultacje ministerialne (Hermes delegate_task) → partie debatują → system zlicza głosy i zwraca PASSED/REJECTED. Ta reguła istnieje w CLI i skills — deploy jej nie modyfikuje.

## Constraints & Preserved Behavior

- parliament CLI i Hermes subprocess launcher muszą działać bez modyfikacji na serwerze PaaS
- /stream/{session_id} i /health kontrakt SSE (format eventów) nie zmienia się
- SQLite schema (sessions, utterances, votes, bill_drafts) zachowana bez migracji
- skills/ katalog (marszalek-sejmu, ministerstwa, partie) nie jest częścią tej zmiany
- Klucze API wyłącznie przez env vars — nigdy hardcoded

## Non-Functional Requirements

- UI ładuje się w ≤2 sekundy (Next.js static shell, bez symulacji) — mierzalne przez jury przy pierwszym wejściu na stronę

## Non-Goals

- Brak auth / kont użytkowników — demo otwarte; logowanie poza zakresem tej zmiany
- Brak obsługi wielu równoczesnych sesji / kolejki — jedna symulacja na raz; dla demo wystarczy
- Brak migracji bazy danych — SQLite schema niezmieniona

## Quality Cross-Check

Access Control:        present — otwarty dostęp, klucze API przez env vars
Business Logic:        present — infrastructure-only (no domain logic change; istniejąca reguła zachowana)
Project artifacts:     present — shape-notes.md z pełnym checkpointem
Timeline-cost ack:     present — 4 dni, user potwierdził wykonalność
Non-Goals:             present — 3 jawne non-goals
Preserved behavior:    present — CLI, SSE kontrakt, SQLite schema, skills/
