/**
 * AiLine Demo Video Recorder — v2 (synced to 128s narration)
 * Uses Playwright with native video recording to capture a real
 * navigated demo of the application running in Docker Compose.
 */
import { chromium } from 'playwright';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BASE = 'http://localhost:3011/en';
const VIDEO_DIR = join(__dirname, 'video-raw');

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function smoothScroll(page, distance, duration = 2000) {
  await page.evaluate(([d, dur]) => {
    return new Promise(resolve => {
      const start = window.scrollY;
      const startTime = performance.now();
      function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / dur, 1);
        const ease = progress < 0.5
          ? 2 * progress * progress
          : -1 + (4 - 2 * progress) * progress;
        window.scrollTo(0, start + d * ease);
        if (progress < 1) requestAnimationFrame(step);
        else resolve();
      }
      requestAnimationFrame(step);
    });
  }, [distance, duration]);
}

(async () => {
  console.log('Launching browser with video recording (v2 — 128s target)...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: VIDEO_DIR,
      size: { width: 1280, height: 720 },
    },
  });

  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  const t0 = Date.now();
  const elapsed = () => ((Date.now() - t0) / 1000).toFixed(1);

  try {
    // === 0:00–0:20  LANDING PAGE (hero, stats, how-it-works) ===
    console.log(`[${elapsed()}s] 1/12 Landing page...`);
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await sleep(4000);                     // hero hold
    await smoothScroll(page, 450, 2000);   // scroll to stats
    await sleep(3000);
    await smoothScroll(page, 450, 2000);   // scroll to how-it-works
    await sleep(3000);
    await smoothScroll(page, 500, 2000);   // features
    await sleep(3000);

    // === 0:20–0:35  DEMO LOGIN + PROFILES ===
    console.log(`[${elapsed()}s] 2/12 Demo login...`);
    await smoothScroll(page, 500, 2000);   // demo login section
    await sleep(3000);
    // Click teacher card
    const teacherCard = page.locator('text=Ms. Sarah Johnson').first();
    if (await teacherCard.isVisible({ timeout: 3000 }).catch(() => false)) {
      await teacherCard.click();
      await sleep(4000);
    } else {
      await page.goto(`${BASE}/dashboard`, { waitUntil: 'domcontentloaded' });
      await sleep(4000);
    }

    // === 0:35–0:50  DASHBOARD ===
    console.log(`[${elapsed()}s] 3/12 Dashboard...`);
    await sleep(3000);
    await smoothScroll(page, 400, 2000);
    await sleep(3000);
    await smoothScroll(page, 400, 2000);
    await sleep(2000);

    // === 0:50–1:00  PLANS ===
    console.log(`[${elapsed()}s] 4/12 Plans...`);
    await page.goto(`${BASE}/plans`, { waitUntil: 'domcontentloaded' });
    await sleep(4000);
    await smoothScroll(page, 300, 1500);
    await sleep(3000);

    // === 1:00–1:12  GUIDE ===
    console.log(`[${elapsed()}s] 5/12 Interactive guide...`);
    await page.goto(`${BASE}/guide`, { waitUntil: 'domcontentloaded' });
    await sleep(3000);
    const tabs = page.locator('[role="tab"]');
    const tabCount = await tabs.count();
    for (let i = 1; i < Math.min(tabCount, 4); i++) {
      await tabs.nth(i).click();
      await sleep(2000);
    }
    await sleep(2000);

    // === 1:12–1:25  ACCESSIBILITY ===
    console.log(`[${elapsed()}s] 6/12 Accessibility...`);
    await page.goto(`${BASE}/accessibility`, { waitUntil: 'domcontentloaded' });
    await sleep(3000);
    await smoothScroll(page, 500, 2000);
    await sleep(3000);
    await smoothScroll(page, 500, 2000);   // digital twin
    await sleep(3000);

    // === 1:25–1:35  TUTOR ===
    console.log(`[${elapsed()}s] 7/12 Tutor chat...`);
    await page.goto(`${BASE}/tutor`, { waitUntil: 'domcontentloaded' });
    await sleep(3000);
    const chatInput = page.locator('textarea, input[type="text"]').last();
    if (await chatInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await chatInput.fill('');
      await chatInput.type('How do I teach fractions to a student with ADHD?', { delay: 50 });
      await sleep(3000);
    }

    // === 1:35–1:45  OBSERVABILITY ===
    console.log(`[${elapsed()}s] 8/12 Observability...`);
    await page.goto(`${BASE}/observability`, { waitUntil: 'domcontentloaded' });
    await sleep(4000);
    await smoothScroll(page, 400, 2000);
    await sleep(3000);

    // === 1:45–1:55  SIGN LANGUAGE ===
    console.log(`[${elapsed()}s] 9/12 Sign language...`);
    await page.goto(`${BASE}/sign-language`, { waitUntil: 'domcontentloaded' });
    await sleep(4000);
    await smoothScroll(page, 400, 2000);
    await sleep(3000);

    // === 1:55–2:08  PERSONA THEMES ===
    console.log(`[${elapsed()}s] 10/12 Persona themes...`);
    await page.goto(`${BASE}/accessibility`, { waitUntil: 'domcontentloaded' });
    await sleep(2000);
    const personas = ['ASD', 'ADHD', 'Dyslexia', 'High Contrast'];
    for (const persona of personas) {
      const btn = page.locator('button, [role="button"]')
        .filter({ hasText: new RegExp(persona, 'i') }).first();
      if (await btn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await btn.click();
        await sleep(2500);
      }
    }

    // === FINAL HOLD — back to landing ===
    console.log(`[${elapsed()}s] 11/12 Return to landing...`);
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await sleep(4000);

    console.log(`[${elapsed()}s] 12/12 Final hold...`);
    await sleep(3000);

  } catch (err) {
    console.error('Navigation error (continuing):', err.message);
  }

  console.log(`Total recording time: ${elapsed()}s`);
  console.log('Closing browser and saving video...');
  const videoPath = await page.video()?.path();
  await context.close();
  await browser.close();

  console.log(`Video saved to: ${videoPath || VIDEO_DIR}`);
})();
