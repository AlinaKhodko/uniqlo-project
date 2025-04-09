const puppeteer = require('puppeteer'); // or 'puppeteer'
const fs = require('fs');
const path = require('path');
const yargs = require('yargs');

const argv = yargs
  .option('url', {
    alias: 'u',
    type: 'string',
    default: 'https://www.uniqlo.com/de/de/feature/sale/women',
    description: 'URL to scrape'
  })
  .option('output', {
    alias: 'o',
    type: 'string',
    default: 'product-ids/uniqlo-raw.html',
    description: 'Path to save raw HTML'
  })
  .help()
  .argv;

(async () => {
const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1400,1000']
  });


  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 1000 });

  await page.setUserAgent(
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
  );

  console.log(`🌍 Navigating to ${argv.url}`);
  await page.goto(argv.url, { waitUntil: 'networkidle2' });

  // ✅ Accept cookies
  try {
    await page.waitForSelector('button#onetrust-accept-btn-handler', { timeout: 5000 });
    await page.click('button#onetrust-accept-btn-handler');
    console.log('✅ Accepted cookies');
  } catch {
    console.log('ℹ️ No cookie popup found');
  }

  // 🔁 Scroll loop
  let previousCount = 0;
  let stableCounter = 0;
  const maxStable = 4;
  const maxScrolls = 100;

  for (let i = 0; i < maxScrolls && stableCounter < maxStable; i++) {
    const currentCount = await page.evaluate(() =>
      document.querySelectorAll('[data-testid="productTile"]').length
    );
    console.log(`⬇️ Scroll ${i + 1}: ${currentCount} products loaded`);

    if (currentCount === previousCount) {
      stableCounter++;
    } else {
      stableCounter = 0;
      previousCount = currentCount;
    }

    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });
    await new Promise(resolve => setTimeout(resolve, 3000));
  }

  console.log('✅ Finished scrolling');

  // 📆 Add timestamp (adjusted for UTC+3)
  const now = new Date();
  now.setHours(now.getHours() + 3); // ⏱ shift by 3 hours
  const timestampComment = `<!-- Fetched on ${now.toISOString()} -->\n`;

  const html = await page.content();
  fs.writeFileSync(path.resolve(argv.output), timestampComment + html, 'utf8');
  console.log(`💾 Saved to ${argv.output}`);

  await browser.close();
})();
