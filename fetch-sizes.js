const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');
const { parse } = require('json2csv');

const INPUT_CSV = 'product-ids/filtered-uniqlo-products.csv';
const OUTPUT_CSV = 'product-ids/uniqlo-with-sizes.csv';
const N = 100; // Number of products to process

async function extractColorAndSizes(url, browser) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 1000 });
  await page.setUserAgent(
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
  );

  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 20000 });

    // ✅ Accept cookies
    try {
      await page.waitForSelector('button#onetrust-accept-btn-handler', { timeout: 5000 });
      await page.click('button#onetrust-accept-btn-handler');
      await page.waitForTimeout(1000);
    } catch {}

    // ✅ Extract selected color
    const color = await page.evaluate(() => {
      const el = Array.from(document.querySelectorAll('p'))
        .find(p => p.textContent?.trim().startsWith('Farbe:'));
      if (!el) return null;
      const text = el.textContent.trim(); // e.g., "Farbe: 09 SCHWARZ"
      return text.split(' ').slice(2).join(' '); // extract "SCHWARZ"
    });

    // ✅ Extract sizes (only available)
    await page.waitForSelector('#product-size-picker input[aria-label]', { timeout: 10000 });

    const sizes = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('#product-size-picker input[aria-label]'))
        .map(input => {
          const label = input.getAttribute('aria-label');
          if (label) {
            const [size, status] = label.split('(');
            const available = !(status?.toLowerCase().includes('unavailable'));
            return available ? size.trim() : null;
          }
          return null;
        })
        .filter(Boolean);
    });

    await page.close();

    console.log(`🟡 Color: ${color || 'Unknown'}`);
    console.log(`✅ Sizes: ${sizes.join(', ') || 'None'}`);

    return color && sizes.length > 0 ? `${color}: ${sizes.join(', ')}` : null;
  } catch (err) {
    console.error(`❌ Failed to scrape ${url}: ${err.message}`);
    await page.close();
    return null;
  }
}

(async () => {
  const rows = [];

  // ✅ Read CSV
  await new Promise((resolve, reject) => {
    fs.createReadStream(path.join(__dirname, INPUT_CSV))
      .pipe(csv())
      .on('data', row => rows.push(row))
      .on('end', resolve)
      .on('error', reject);
  });

  const browser = await puppeteer.launch({
    headless: 'new', // or true
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1400,1000']
  });

  for (let i = 0; i < Math.min(N, rows.length); i++) {
    const row = rows[i];
    const urls = row['Color Variant URLs']
      ? row['Color Variant URLs'].split('|').map(url => url.trim()).filter(Boolean)
      : [];

    const variants = [];

    console.log(`\n🔍 ${row['Product Name']} (${urls.length} color variants)`);

    for (const url of urls) {
      console.log(`🌐 ${url}`);
      const result = await extractColorAndSizes(url, browser);
      if (result) variants.push(result);
    }

    row['Available Sizes'] = variants.join(' | ') || 'Unavailable';

    // 💾 Save after every product
    const csvOutput = parse(rows, { fields: Object.keys(rows[0]) });
    fs.writeFileSync(path.join(__dirname, OUTPUT_CSV), csvOutput, 'utf8');
    console.log(`💾 Saved progress after "${row['Product Name']}"`);
  }

  await browser.close();
  console.log(`\n✅ Final CSV saved to ${OUTPUT_CSV}`);
})();
