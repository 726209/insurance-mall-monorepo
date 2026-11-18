#!/usr/bin/env node
/**
 * Record the running application, without changing its business responses.
 * Requires playwright-core, Google Chrome and ffmpeg; see README.md.
 * Only chat threads created during this recording are shown in the sidebar.
 */
import { mkdir, mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';

const moduleName = process.env.HM_DEMO_PLAYWRIGHT_MODULE || 'playwright-core';
const { chromium } = await import(
  path.isAbsolute(moduleName) ? pathToFileURL(moduleName).href : moduleName
);
const baseURL = process.env.HM_DEMO_BASE_URL || 'http://localhost:5173';
const chromePath = process.env.HM_DEMO_CHROME ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const assetDir = fileURLToPath(new URL('../assets/', import.meta.url));
const frameRoot = await mkdtemp(path.join(tmpdir(), 'hm-insurance-demo-'));
const sections = new Set((process.env.HM_DEMO_SECTIONS || 'catalog,advisor,plan,claims,threads').split(','));
const createdThreads = new Set();
const manifest = { recordedAt: new Date().toISOString(), baseURL, mode: 'live', viewport: { width: 1440, height: 960 }, sections: [], createdThreadIds: [] };
try {
  const previous = JSON.parse(await readFile(new URL('./demo-manifest.json', import.meta.url), 'utf8'));
  manifest.sections = previous.sections || [];
  for (const id of previous.createdThreadIds || []) createdThreads.add(id);
} catch { /* First recording has no previous manifest. */ }
await mkdir(assetDir, { recursive: true });

function command(program, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(program, args, { stdio: ['ignore', 'ignore', 'pipe'] });
    let error = '';
    child.stderr.on('data', (chunk) => { error += chunk; });
    child.on('error', reject);
    child.on('close', (code) => code === 0 ? resolve() : reject(new Error(error.slice(-2500))));
  });
}

const browser = await chromium.launch({ executablePath: chromePath, headless: true });
const context = await browser.newContext({ viewport: manifest.viewport, deviceScaleFactor: 1, locale: 'zh-CN', reducedMotion: 'reduce' });
if (process.env.HM_DEMO_DEMO_SESSION === '1') {
  await context.addInitScript(() => localStorage.setItem('insurance-mall-auth-v2', JSON.stringify({ user: { id: 1, username: 'heima', displayName: '教学演示' } })));
}
const page = await context.newPage();
page.setDefaultTimeout(20000);

// Filter out pre-existing chat threads for recording privacy. All retained
// records and all product, message and tool responses come from the real API.
await context.route('**/api/v1/chat-threads', async (route) => {
  const response = await route.fetch();
  if (route.request().method() === 'GET' && response.ok()) {
    const data = await response.json();
    await route.fulfill({ response, json: data.filter((item) => createdThreads.has(item.id)) });
  } else {
    if (route.request().method() === 'POST' && response.ok()) {
      const data = await response.json();
      createdThreads.add(data.id);
    }
    await route.fulfill({ response });
  }
});

const hold = (milliseconds) => page.waitForTimeout(milliseconds);
async function caption(text) {
  await page.evaluate((label) => {
    let element = document.getElementById('readme-demo-caption');
    if (!element) {
      element = document.createElement('div');
      element.id = 'readme-demo-caption';
      Object.assign(element.style, { position: 'fixed', right: '18px', bottom: '14px', zIndex: '2147483647', padding: '10px 16px', background: '#102c4f', color: '#fff', borderRadius: '9px', font: '600 16px sans-serif', boxShadow: '0 3px 14px #0002', pointerEvents: 'none' });
      document.body.append(element);
    }
    element.textContent = label;
  }, text);
}

async function recording(name, title, action) {
  console.log(`START ${name}`);
  const frameDir = path.join(frameRoot, name);
  await mkdir(frameDir, { recursive: true });
  await caption(title);
  let running = true;
  let index = 0;
  let lastHash = '';
  let identicalFrames = 0;
  let skippedIdleFrames = 0;
  const capturing = (async () => {
    while (running) {
      const started = Date.now();
      try {
        const buffer = await page.screenshot({ animations: 'disabled' });
        const hash = createHash('sha256').update(buffer).digest('hex');
        identicalFrames = hash === lastHash ? identicalFrames + 1 : 0;
        lastHash = hash;
        // Compress unchanged waiting screens; do not alter replies or API data.
        if (identicalFrames <= 5) {
          await writeFile(path.join(frameDir, `frame-${String(index).padStart(5, '0')}.png`), buffer);
          index += 1;
        } else skippedIdleFrames += 1;
      } catch (error) {
        if (running) console.log(`CAPTURE ${error.message.split('\n')[0]}`);
      }
      await new Promise((resolve) => setTimeout(resolve, Math.max(20, 500 - (Date.now() - started))));
    }
  })();
  const result = { name, title, status: 'recorded' };
  try {
    await hold(1200);
    await action(result);
    await hold(1800);
  } catch (error) {
    result.status = 'partial';
    result.error = error.message.split('\n')[0];
    console.log(`PARTIAL ${name}: ${result.error}`);
    for (const selector of ['.ant-modal-close', '.ant-drawer-close']) {
      const close = page.locator(selector).last();
      if (await close.isVisible().catch(() => false)) await close.click().catch(() => {});
    }
  } finally {
    running = false;
    await capturing;
    result.frames = index;
    result.skippedIdleFrames = skippedIdleFrames;
    if (index) {
      await command('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-framerate', '2', '-i', path.join(frameDir, 'frame-%05d.png'), '-filter_complex', '[0:v]scale=1200:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle', '-loop', '0', path.join(assetDir, `${name}.gif`)]);
      result.asset = `docs/assets/${name}.gif`;
    }
    manifest.sections = [...manifest.sections.filter((item) => item.name !== name), result];
    manifest.createdThreadIds = [...createdThreads];
    await writeFile(new URL('./demo-manifest.json', import.meta.url), JSON.stringify(manifest, null, 2) + '\n');
    console.log(`DONE ${name}: ${index} frames, ${result.status}`);
  }
}

async function click(locator) {
  await locator.scrollIntoViewIfNeeded();
  const rect = await locator.boundingBox();
  if (rect) await page.mouse.move(rect.x + rect.width / 2, rect.y + rect.height / 2, { steps: 8 });
  await hold(250);
  await locator.click();
  await hold(700);
}

async function renameActive(title) {
  await click(page.locator('.thread-item.is-active .thread-actions button').first());
  await page.getByPlaceholder('请输入会话名称').fill(title);
  await click(page.getByRole('dialog').getByRole('button', { name: /保\s*存/ }));
}

async function newThread(title) {
  await click(page.getByRole('button', { name: '新建咨询' }));
  await renameActive(title);
}

async function send(message) {
  const input = page.locator('.chat-composer textarea');
  await input.fill(message);
  await hold(700);
  await click(page.getByRole('button', { name: /发\s*送/ }));
  await input.waitFor({ state: 'visible' });
  await page.waitForFunction(() => !document.querySelector('.chat-composer textarea')?.disabled, undefined, { timeout: 150000 });
  await hold(1400);
}

try {
  await page.goto(baseURL, { waitUntil: 'networkidle' });
  await page.locator('.product-card').first().waitFor();

  if (sections.has('catalog')) await recording('01-product-catalog', '01 / 商城：产品分类与详情', async () => {
    await click(page.locator('.ant-segmented-item').filter({ hasText: '重疾险' }));
    await page.locator('.products-alert').waitFor({ state: 'hidden' });
    await page.getByText('共 3 款产品', { exact: true }).waitFor();
    await click(page.locator('.product-card').filter({ hasText: '达尔文12号重大疾病保险' }).getByRole('button', { name: /查看详情/ }));
    await hold(2200);
    await click(page.locator('.ant-modal-close'));
    await click(page.locator('.ant-segmented-item').filter({ hasText: '医疗险' }));
    await page.locator('.products-alert').waitFor({ state: 'hidden' });
    await hold(1500);
    await click(page.locator('.ant-segmented-item').filter({ hasText: '意外险' }));
    await page.locator('.products-alert').waitFor({ state: 'hidden' });
    await hold(1500);
    await click(page.locator('.ant-segmented-item').filter({ hasText: '全部' }));
    await page.getByText('共 12 款产品', { exact: true }).waitFor();
    await page.locator('.products-alert').waitFor({ state: 'hidden' });
    await page.evaluate(() => document.getElementById('readme-demo-caption')?.remove());
    await page.screenshot({ path: path.join(assetDir, 'home.png') });
    await caption('01 / 商城：产品分类与详情');
  });

  await click(page.getByRole('button', { name: '让顾问帮我选' }));
  if (await page.getByRole('dialog').isVisible().catch(() => false)) {
    await click(page.getByRole('dialog').getByRole('button', { name: '登录', exact: true }));
  }
  await page.locator('.chat-composer textarea').waitFor();
  if (!await page.locator('.thread-item.is-active').isVisible().catch(() => false)) {
    await hold(1800);
    if (!await page.locator('.thread-item.is-active').isVisible().catch(() => false)) {
      await click(page.getByRole('button', { name: '新建咨询' }));
    }
  }
  await page.locator('.thread-item.is-active').waitFor();

  if (sections.has('advisor')) await recording('02-clause-citations', '02 / 智能顾问：真实检索与条款引用', async (result) => {
    await renameActive('演示·条款检索');
    await send('达尔文12号重大疾病保险的等待期是多久？请查询该产品条款，简短回答并附引用。');
    const source = page.locator('.source-list button').first();
    result.hasCitations = await source.isVisible().catch(() => false);
    if (!result.hasCitations) throw new Error('本次回复没有可点击条款引用，请检查模型/RAG配置');
    await click(source);
    await page.getByText('条款引用', { exact: true }).waitFor();
    await hold(3500);
    await page.screenshot({ path: path.join(assetDir, 'clause-citation.png') });
    await click(page.locator('.ant-drawer-close'));
  });

  if (sections.has('plan')) await recording('03-plan-confirmation', '03 / 保险方案：推荐、确认与保存', async (result) => {
    await newThread('演示·方案确认');
    await send('我30岁，办公室职员，身体健康，无既往症。请查询意外险候选，只推荐太平洋小蜜蜂6号综合意外险，年预算200元，简短说明即可。');
    await send('请调用保存方案工具，将刚才推荐的小蜜蜂6号保存为“演示·意外保障方案”。按已查询到的真实产品ID填写，单项优先级1，年缴预算200元；让我在确认卡中决定是否保存。');
    const approve = page.getByRole('button', { name: /确认保存方案/ });
    result.hasConfirmation = await approve.isVisible().catch(() => false);
    if (!result.hasConfirmation) throw new Error('本次模型没有触发方案确认卡');
    await hold(3000);
    await page.screenshot({ path: path.join(assetDir, 'plan-confirmation.png') });
    await click(approve);
    await page.waitForFunction(() => !document.querySelector('.chat-composer textarea')?.disabled, undefined, { timeout: 120000 });
    await hold(2000);
    result.savedReplyVisible = await page.getByText(/保存成功|已保存|成功保存/).first().isVisible().catch(() => false);
  });

  if (sections.has('claims')) await recording('04-claim-guidance', '04 / 理赔顾问：材料与报案流程指引', async (result) => {
    await newThread('演示·理赔指引');
    await send('医疗险住院理赔通常需要准备哪些材料？请查询理赔指引并简短说明，不查询我的保单或案件。');
    result.hasReply = (await page.locator('.chat-message--assistant').last().innerText()).length > 10;
    await hold(2200);
  });

  if (sections.has('threads')) await recording('05-thread-management', '05 / 会话管理：新建、重命名、历史与删除', async (result) => {
    await newThread('演示·可删除的空会话');
    await hold(1400);
    const historyThread = page.locator('.thread-item').filter({ hasText: '演示·条款检索' });
    if (await historyThread.count()) {
      await click(historyThread.locator('button').first());
      await hold(2500);
    }
    const emptyThread = page.locator('.thread-item').filter({ hasText: '演示·可删除的空会话' });
    await click(emptyThread.locator('.thread-actions button').last());
    await click(page.locator('.ant-popover').getByRole('button', { name: /删\s*除/ }));
    result.deletedOwnEmptyThread = await emptyThread.count() === 0;
    await hold(1800);
  });
} finally {
  manifest.createdThreadIds = [...createdThreads];
  manifest.sections.sort((a, b) => a.name.localeCompare(b.name));
  await browser.close();
  const sequence = ['01-product-catalog', '02-clause-citations', '03-plan-confirmation', '04-claim-guidance', '05-thread-management'];
  if (sequence.every((name) => manifest.sections.some((item) => item.name === name && item.status === 'recorded'))) {
    const inputs = sequence.flatMap((name) => ['-ignore_loop', '1', '-i', path.join(assetDir, `${name}.gif`)]);
    const normalize = sequence.map((_, index) => `[${index}:v]fps=2,format=rgba[v${index}];`).join('');
    const sources = sequence.map((_, index) => `[v${index}]`).join('');
    await command('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...inputs, '-filter_complex', `${normalize}${sources}concat=n=5:v=1:a=0,split[a][b];[a]palettegen=max_colors=160:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle`, '-loop', '0', path.join(assetDir, 'project-demo.gif')]);
    manifest.overview = { asset: 'docs/assets/project-demo.gif', sections: sequence };
  }
  await writeFile(new URL('./demo-manifest.json', import.meta.url), JSON.stringify(manifest, null, 2) + '\n');
  console.log(`Raw frames kept in ${frameRoot}`);
}
