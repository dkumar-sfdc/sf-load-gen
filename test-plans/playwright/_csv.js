// Minimal quoted-CSV reader (no deps). Returns array of row objects keyed by header.
const fs = require('fs');

function parseLine(line) {
  const out = [];
  let cur = '', inQ = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (inQ) {
      if (c === '"' && line[i + 1] === '"') { cur += '"'; i++; }
      else if (c === '"') inQ = false;
      else cur += c;
    } else if (c === '"') inQ = true;
    else if (c === ',') { out.push(cur); cur = ''; }
    else cur += c;
  }
  out.push(cur);
  return out;
}

function readCsv(path) {
  const lines = fs.readFileSync(path, 'utf8').split(/\r?\n/).filter(l => l.trim().length);
  const headers = parseLine(lines.shift());
  return lines.map(l => {
    const cells = parseLine(l);
    return Object.fromEntries(headers.map((h, i) => [h.trim(), cells[i]]));
  });
}

module.exports = { readCsv };
