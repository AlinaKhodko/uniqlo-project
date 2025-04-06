const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');

const filePath = path.join(__dirname, 'product-ids/uniqlo-raw.html');
const html = fs.readFileSync(filePath, 'utf8');

// ✅ Extract timestamp from HTML comment
const timestampMatch = html.match(/<!--\s*Fetched on ([\d\-T:.Z]+)\s*-->/);
const fetchedAt = timestampMatch ? timestampMatch[1] : 'Unknown';

const $ = cheerio.load(html);

// 📦 CSV rows (no Sizes column now)
const baseUrl = 'https://www.uniqlo.com';
const rows = [['Product ID', 'Product Name', 'Price (Promo)', 'Price (Original)', 'Rating', 'Reviews', 'Product URL', 'Color Variant URLs', 'Fetched At']];
const seen = new Set();

$('.fr-ec-product-tile__end').each((_, el) => {
  const $el = $(el);

  const name = $el.find('[data-testid="CoreTitle"]').text().trim();
  const promoPrice = $el
    .find('.fr-ec-price-text--middle')
    .first()
    .text()
    .trim()
    .replace(/\s*â‚¬|€/g, '€');
  const originalPrice = $el
    .find('.fr-ec-price__strike-through')
    .first()
    .text()
    .trim()
    .replace(/\s*â‚¬|€/g, '€');
  const rating = $el
    .find('.fr-ec-rating-average-product-tile')
    .first()
    .text()
    .trim();
  const reviews = $el
    .find('.fr-ec-rating-static__count-product-tile')
    .first()
    .text()
    .trim()
    .replace(/[()]/g, '');

  // ✅ Product ID and link
  let productId = '';
  let productHref = '';
  const parentLink = $el.closest('a[id][href*="/products/"]');
  if (parentLink.length) {
    productId = parentLink.attr('id')?.trim() || '';
    productHref = parentLink.attr('href')?.trim() || '';
  }

  const productURL = productHref ? baseUrl + productHref : '';

  // ✅ Color variant links
  const colorCodes = [];
  $el.closest('.fr-ec-product-tile')
    .find('input[name="shortChipGroup"][aria-label]')
    .each((_, input) => {
      const code = $(input).attr('aria-label');
      if (code) colorCodes.push(code);
    });

  const variantLinks = colorCodes
    .map(code =>
      productURL.includes('?')
        ? `${productURL}&colorDisplayCode=${code}`
        : `${productURL}?colorDisplayCode=${code}`
    )
    .join(' | ');

  if (name && (promoPrice || originalPrice)) {
    const row = [productId, name, promoPrice, originalPrice, rating, reviews, productURL, variantLinks, fetchedAt];
    const rowKey = row.join('|');

    if (!seen.has(rowKey)) {
      seen.add(rowKey);
      rows.push(row);
    }
  }
});

// 💾 Write to CSV
const csv = rows.map(row => row.map(val => `"${val}"`).join(',')).join('\n');
fs.writeFileSync('./data/uniqlo-products.csv', csv, 'utf8');

console.log(`✅ Saved ${rows.length - 1} products to uniqlo-products.csv with timestamp`);
