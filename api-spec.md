Below is the **complete, detailed API specification** for your dummy server, including JWT-based session management (1 year expiry), all protected endpoints, request/response schemas, headers, and error codes. You can implement these stubs immediately in Express, FastAPI, Flask, etc.

---

## 0. Authentication & Session Management

All protected endpoints require:

```
Authorization: Bearer <accessToken>
```

where `<accessToken>` is a JWT with a `sessionId` claim, signed by your server, expiring in **1 year** (31536000 s). Refresh tokens also expire in 1 year.

### 0.1. Create Session

`POST /api/auth/session`

* **Description**
  Issue a new anonymous session. Returns `accessToken` + `refreshToken`.

* **Request**

  * Headers: *none*
  * Body: *none*

* **Response 200**

  ```json
  {
    "accessToken": "<jwt-access-token>",
    "expiresIn": 31536000,
    "refreshToken": "<jwt-refresh-token>",
    "refreshExpiresIn": 31536000
  }
  ```

* **Errors**

  * `500 Internal Server Error` – JWT generation failed.

---

### 0.2. Refresh Token

`POST /api/auth/refresh`

* **Description**
  Exchange a valid refresh token for a new access (and optionally refresh) token.

* **Request**

  * Headers: *none*
  * Body:

    ```json
    {
      "refreshToken": "<jwt-refresh-token>"
    }
    ```

* **Response 200**

  ```json
  {
    "accessToken": "<new-jwt-access-token>",
    "expiresIn": 31536000,
    "refreshToken": "<new-jwt-refresh-token>",
    "refreshExpiresIn": 31536000
  }
  ```

* **Errors**

  * `400 Bad Request` – missing or malformed body.
  * `401 Unauthorized` – invalid/expired refresh token.
  * `500 Internal Server Error` – JWT rotation failed.

---

### 0.3. Revoke Session (Optional)

`DELETE /api/auth/session`

* **Description**
  Revoke (blacklist) a refresh token, ending the session.

* **Request**

  * Headers:

    ```
    Authorization: Bearer <accessToken>
    ```
  * Body:

    ```json
    {
      "refreshToken": "<jwt-refresh-token>"
    }
    ```

* **Response 200**

  ```json
  { "revoked": true }
  ```

* **Errors**

  * `400 Bad Request` – missing token.
  * `401 Unauthorized` – invalid access token.
  * `500 Internal Server Error` – revocation failed.

---

## 1. Goal & Personalization

All endpoints below require a valid `Authorization` header.

### 1.1. Submit Goal

`POST /api/goal`

* **Description**
  Parse raw user input into a structured goal + return initial personalization payload.

* **Request**

  * Headers:

    ```
    Authorization: Bearer <accessToken>
    Content-Type: application/json
    ```
  * Body:

    ```json
    {
      "input": "I want to build an AI agent for restaurants"
    }
    ```

* **Response 200**

  ```json
  {
    "sessionId": "abc123",
    "goal": { /* structured goal */ },
    "missions": [
      { "id":"defineMetrics","title":"Define Success Metrics","points":15 },
      /* … */
    ],
    "headline": "AI Agent for Restaurants: Increase Table Turnover with Contextual Suggestions",
    "recommendedCaseStudies": [
      { "id":"cs1","title":"Booking Optimizer","summary":"Reduced latency by 80%" },
      /* … */
    ]
  }
  ```

* **Errors**

  * `400 Bad Request` – missing or empty `input`.
  * `401 Unauthorized` – invalid/expired access token.
  * `500 Internal Server Error` – LLM parse error.

---

### 1.2. Clarify Goal

`POST /api/clarify`

* **Description**
  Accept one follow-up answer to refine the goal; returns updated personalization.

* **Request**

  * Headers:

    ```
    Authorization: Bearer <accessToken>
    Content-Type: application/json
    ```
  * Body:

    ```json
    {
      "clarification": "Increase customer satisfaction"
    }
    ```

* **Response 200**

  ```json
  {
    "goal": { /* updated goal */ },
    "missions": [ /* updated missions */ ],
    "headline": "...",
    "recommendedCaseStudies": [ /* updated list */ ]
  }
  ```

* **Errors**

  * `400 Bad Request` – missing `clarification`.
  * `401 Unauthorized` – invalid token.
  * `500 Internal Server Error` – clarification parse failure.

---

### 1.3. Fetch Personalized Content

`GET /api/personalised`

* **Description**
  Retrieve all personalized content in one payload.

* **Request**

  * Headers:

    ```
    Authorization: Bearer <accessToken>
    ```

* **Response 200**

  ```json
  {
    "headline": "...",
    "goal": { /* structured goal */ },
    "missions": [
      { "id":"defineMetrics","title":"Define Success Metrics","points":15 },
      /* … */
    ],
    "recommendedCaseStudies": [
      { "id":"cs1","title":"Booking Optimizer","summary":"Reduced latency by 80%" },
      /* … */
    ]
  }
  ```

* **Errors**

  * `401 Unauthorized` – invalid token.
  * `404 Not Found` – session not found.
  * `500 Internal Server Error` – personalization engine error.

---

## 2. Missions & Progress

### 2.1. Get Progress

`GET /api/progress`

* **Description**
  Fetch current mission statuses, total points, and unlock flag.

* **Request**

  * Headers:

    ```
    Authorization: Bearer <accessToken>
    ```

* **Response 200**

  ```json
  {
    "pointsTotal": 45,
    "missions": [
      { "id":"defineMetrics","status":"completed","points":15 },
      { "id":"sketchFlow","status":"pending","points":15 },
      /* … */
    ],
    "callUnlocked": false
  }
  ```

* **Errors**

  * `401 Unauthorized` – invalid token.
  * `404 Not Found` – session missing.
  * `500 Internal Server Error` – scoring engine error.

---

### 2.2. Complete Mission

`POST /api/mission/complete`

* **Description**
  Mark a mission complete, submit artifact, award points, and get updated progress.

* **Request**

  * Headers:

    ```
    Authorization: Bearer <accessToken>
    Content-Type: application/json
    ```
  * Body:

    ```json
    {
      "missionId": "sketchFlow",
      "artifact": {
        "answer": "Flow: Input→Process→Output"
      }
    }
    ```

* **Response 200**

  ```json
  {
    "pointsAwarded": 15,
    "pointsTotal": 60,
    "callUnlocked": false,
    "nextMission": { "id":"runDemo","title":"Run the AI demo" }
  }
  ```

* **Errors**

  * `400 Bad Request` – missing `missionId` or invalid artifact.
  * `401 Unauthorized` – invalid token.
  * `403 Forbidden` – mission already completed or invalid mission.
  * `404 Not Found` – session or mission not found.
  * `500 Internal Server Error` – scoring update failure.

---

### 2.3. Check Unlock Status

`GET /api/unlock-status`

* **Description**
  Quick check whether the free call gate is unlocked.

* **Request**

  * Headers:

    ```
    Authorization: Bearer <accessToken>
    ```

* **Response 200**

  ```json
  { "callUnlocked": true }
  ```

* **Errors**

  * `401 Unauthorized` – invalid token.
  * `404 Not Found` – session not found.

---

## 3. Session Hydration

### 3.1. Get Full Session

`GET /api/session`

* **Description**
  Retrieve the entire session state to hydrate the frontend.

* **Request**

  * Headers:

    ```
    Authorization: Bearer <accessToken>
    ```

* **Response 200**

  ```json
  {
    "goal": { /* ... */ },
    "missions": [
      { "id":"defineMetrics","status":"completed","points":15 },
      /* … */
    ],
    "pointsTotal": 60,
    "callUnlocked": true
  }
  ```

* **Errors**

  * `401 Unauthorized` – invalid token.
  * `404 Not Found` – session missing.
  * `500 Internal Server Error` – session retrieval error.

---

## 4. Error Response Format

All errors return JSON:

```json
{
  "error": {
    "code": 400,
    "message": "Detailed error description."
  }
}
```

* `400 Bad Request` – client-side input error.
* `401 Unauthorized` – missing/invalid/expired access token.
* `403 Forbidden` – action not allowed.
* `404 Not Found` – session or resource not found.
* `500 Internal Server Error` – server-side failure.

---

## 4. Conversational AI

### 4.1. Chat with Assistant

`POST /api/chat`

* **Description**
  Continue the contextual conversation once the personalized micro-site is live. Returns the assistant's reply, the full chat history, and optionally: next missions, progress updates, reading suggestions, and a `navigate` object to direct the frontend to a specific page/section.

* **Request**

  * Headers:

    ```
    Authorization: Bearer <accessToken>
    Content-Type: application/json
    ```
  * Body:

    ```json
    {
      "message": "Which mission should I tackle next?",
      "context": {
        "page": "mission-dashboard",
        "section": "mission-1", 
        "metadata": { "missionId": "defineMetrics" }
      }
    }
    ```

    | Field         | Type     | Required | Description                                                                                    |
    | ------------- | -------- | :------: | ---------------------------------------------------------------------------------------------- |
    | `message`     | `string` |    Yes   | The user's latest chat input.                                                                  |
    | `context`     | `object` |    Yes   | Where the user is on the site, to ground the assistant's reply.                                |
    | ├─ `page`     | `string` |    Yes   | Page identifier, e.g. `"micro-landing"`, `"case-study"`, `"mission-dashboard"`.                |
    | ├─ `section`  | `string` |    Yes   | Subsection/component, e.g. `"hero"`, `"mission-3"`, `"progress-widget"`.                       |
    | └─ `metadata` | `object` |    No    | Any extra state needed, e.g. `{ "caseStudyId": "cs2" }` or `{ "missionId": "defineMetrics" }`. |

* **Response 200**

  ```json
  {
    "reply": "Great—you've completed defining your metrics. Next, sketch the agent's decision flow.",
    "history": [
      { "role":"user",      "message":"Done with metrics.", "timestamp":"2025-08-05T10:00:10Z" },
      { "role":"assistant", "message":"Next, sketch the decision flow for your agent...", "timestamp":"2025-08-05T10:00:12Z" }
    ],
    "updatedProgress": {
      "pointsTotal": 15,
      "missions": [
        { "id":"defineMetrics","status":"completed","points":15 },
        { "id":"sketchFlow","status":"pending","points":15 }
      ],
      "callUnlocked": false
    },
    "followUpMissions": [
      { "id":"sketchFlow","title":"Sketch Agent Flow","points":15 }
    ],
    "suggestedRead": [
      { "id":"cs2","title":"Menu Recommender","summary":"How we boosted upsell by 22%" }
    ],
    "navigate": {
      "page": "mission-dashboard",
      "section": "mission-2",
      "metadata": { "missionId": "sketchFlow" }
    }
  }
  ```

    | Field               | Type            | Description                                                                      |
    | ------------------- | --------------- | -------------------------------------------------------------------------------- |
    | `reply`             | `string`        | The assistant's response text.                                                   |
    | `history`           | `array<object>` | Full chat history so far, each with `{ role, message, timestamp }`.              |
    | `followUpMissions?` | `array<object>` | (Optional) New or reprioritized missions, same schema as `/api/goal`.            |
    | `updatedProgress?`  | `object`        | (Optional) `{ pointsTotal, missions, callUnlocked }` snapshot for UI sync.       |
    | `suggestedRead?`    | `array<object>` | (Optional) Case-study recs: `[ { id, title, summary } ]`.                        |
    | `navigate?`         | `object`        | (Optional) Navigation instruction to the frontend.                               |
    | ├─ `page`           | `string`        | Target page to navigate to (same identifiers as in request).                     |
    | ├─ `section`        | `string`        | Specific section or component on that page.                                      |
    | └─ `metadata?`      | `object`        | Any parameters needed for that navigation, e.g. `{ "missionId": "sketchFlow" }`. |

* **Errors**

  * `400 Bad Request` – Missing or malformed `message`/`context` fields.
  * `401 Unauthorized` – Missing, invalid, or expired access token.
  * `404 Not Found` – Session not found.
  * `500 Internal Server Error` – AI Assistant or backend failure.

---

### Summary Table

| Method | Path                    | Description                                         |
| ------ | ----------------------- | --------------------------------------------------- |
| POST   | `/api/auth/session`     | Create session → JWT + refresh token                |
| POST   | `/api/auth/refresh`     | Rotate refresh token → new JWT                      |
| DELETE | `/api/auth/session`     | Revoke refresh token (optional)                     |
| POST   | `/api/goal`             | Parse user goal → structured goal + personalization |
| POST   | `/api/clarify`          | Refine goal via follow-up                           |
| GET    | `/api/personalised`     | Fetch all personalized content                      |
| GET    | `/api/progress`         | Get points, mission statuses, unlock flag           |
| POST   | `/api/mission/complete` | Complete mission + award points + next mission      |
| GET    | `/api/unlock-status`    | Check if call gate unlocked                         |
| GET    | `/api/session`          | Hydrate full session state                          |
| POST   | `/api/chat`             | Chat with AI assistant (contextual conversation)    |

---

With this spec you can build a dummy API server that returns static or randomized JSON matching these schemas. The frontend can immediately integrate and mock flows end-to-end, then replace stubs with real logic as you build out each backend component.
