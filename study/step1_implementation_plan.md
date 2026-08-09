# Implementation Plan: Step 1 - Prepare the Frontend for Vercel

This plan details the steps to build a premium, user-facing web dashboard using React/Next.js, replacing the local Streamlit application. This frontend will run on Vercel's free tier and communicate with our containerized backend.

## Proposed Changes

We will create a Next.js application inside a new `frontend` folder in the root directory.

### [Component 1] Next.js Project Structure

#### [NEW] [frontend/package.json](file:///c:/Users/KIIT/Desktop/AutoML/frontend/package.json)
* Dependencies: `react`, `react-dom`, `next`, `lucide-react` (for icons).

#### [NEW] [frontend/app/layout.js](file:///c:/Users/KIIT/Desktop/AutoML/frontend/app/layout.js)
* Configures global font loaders (Inter/Outfit), metadata, and HTML container structures.

#### [NEW] [frontend/app/page.js](file:///c:/Users/KIIT/Desktop/AutoML/frontend/app/page.js)
* Main application interface, housing:
  * File uploader state and target variable inputs.
  * Status steps tracker (Idle → Uploading → Profiling → Code Gen → Training → Complete).
  * Real-time console logger showing stdout/stderr tracebacks from the sandbox.
  * Download card for the final `.zip` bundle.

#### [NEW] [frontend/app/globals.css](file:///c:/Users/KIIT/Desktop/AutoML/frontend/app/globals.css)
* Implements the design system:
  * Sleek dark-mode aesthetic with dark indigo background (`#0b0f19`).
  * Vibrant gradient accent glows (indigo to violet).
  * Micro-animations for buttons, drag-and-drop hover zones, and status loaders.

---

## Technical Flow & State Management

1. **User Uploads Dataset:** File is selected. A request is made to the backend to get a Supabase Storage upload URL, or uploaded directly depending on backend configuration.
2. **Execution Trigger:** User enters `target_variable` and triggers the AutoML run.
3. **Pipeline Progress Polling / SSE:** The frontend listens to progress events or polls the status, dynamically lighting up dashboard steps and outputting agent tracebacks to the console logger.
4. **Completion:** A download button points to the generated zip bundle URL.

---

## Verification Plan

### Manual Verification
* Run the Next.js development server locally:
  ```bash
  cd frontend
  npm run dev
  ```
* Verify layout responsiveness on mobile and desktop viewports.
* Verify drag-and-drop states (drag over, drag leave, file accepted).
* Mock backend responses to test the status tracker and traceback log rendering.
