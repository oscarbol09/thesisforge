const assert = require('node:assert/strict');
const fs = require('node:fs');
const {resolve} = require('node:path');
const vm = require('node:vm');

const first = {title: 'Shared  title', authors: ['Ana Author'], url: 'https://example.org/works/1', venue: 'Journal A'};
const same = {...first, title: 'shared title', authors: ['ana author'], year: null};
const spanish = {...first, title: 'Historia de la educación', authors: ['María Núñez'], venue: null};
const scenarios = [
  ['same-spanish', spanish, {...spanish}, true],
  ['spanish-different-author', spanish, {...spanish, authors: ['Lucía Núñez']}, false],
  ['spanish-different-path', spanish, {...spanish, url: 'https://example.org/works/2'}, false],
  ['spanish-different-year', {...spanish, year: 1999}, {...spanish, year: 1781}, false],
  ['spanish-different-journal', {...spanish, venue: 'Journal A'}, {...spanish, venue: 'Journal B'}, false],
  ['spanish-different-doi', {...spanish, doi: '10.1234/one'}, {...spanish, doi: '10.1234/two'}, false],
  ['casefold-server', {...first, title: 'Straße'}, {...first, title: 'STRASSE'}, false, true],
  ['blank-unicode-title', {...spanish, title: '\u0085\u00a0'}, {...spanish, title: '\u0085\u00a0'}, false],
  ['blank-unicode-author', {...spanish, authors: ['\u0085\u00a0']}, {...spanish, authors: ['\u0085\u00a0']}, false],

  ['different-doi', {...first, doi: '10.1234/one'}, {...first, doi: '10.1234/two'}, false],
  ['same-doi', {...first, doi: '10.1234/ONE'}, {...first, doi: '10.1234/one'}, true],
  ['different-author', first, {...first, authors: ['Ben Author']}, false],
  ['different-year', first, {...first, year: 1781}, false],
  ['same-no-doi', first, {...same, source: 'openalex', url: 'http://WWW.EXAMPLE.ORG/works/1/#details'}, true],
  ['different-journal', first, {...same, venue: 'Journal B'}, false],
  ['different-path', first, {...same, url: 'https://example.org/works/2'}, false],
  ['missing-author', first, {...first, authors: []}, false],
  ['internal-bom', {...first, title: 'Alpha\uFEFFBeta'}, {...first, title: 'Alpha Beta'}, false],
  ['unicode-space', {...first, title: 'Alpha\u0085Beta'}, {...first, title: 'Alpha Beta'}, false, true],
  ['dot-segment', {...first, url: 'https://example.org/a/../b'}, {...first, url: 'https://example.org/b'}, false],
  ['encoded-dot-segment', {...first, url: 'https://example.org/a/%2e%2e/b'}, {...first, url: 'https://example.org/b'}, false],
  ['one-doi', first, {...first, doi: '10.1234/one'}, false],
];

async function templateClick(script, project, paper, force = false) {
  const [, click, disabled] = script.match(/@click="(addCitationToProject\(paper\))"\s+:disabled="([^"]+)"/);
  const requests = [];
  const app = {
    activeProject: project,
    api: async (path, options) => requests.push({path, ...options}),
    toast() {},
    async refreshActiveProject() {},
  };
  const context = vm.createContext({Alpine: {store: () => app}, URL, paper});
  vm.runInContext(script + '\nconst component = literatureComponent();', context);
  const blocked = vm.runInContext('component.' + disabled, context);
  if (force || !blocked) await vm.runInContext('component.' + click, context);
  return {click, disabled, blocked, requests};
}

async function main() {
  const [path = resolve(__dirname, '../../gui/js/literature.js'), mode, input] = process.argv.slice(2);
  if (mode === 'scenarios') {
    console.log(JSON.stringify(scenarios));
    return;
  }
  const script = fs.readFileSync(path, 'utf8');
  if (mode === 'click') {
    const {project, paper, force} = JSON.parse(input);
    console.log(JSON.stringify(await templateClick(script, project, paper, force)));
    return;
  }
  const results = [];
  for (const [name, initial, second, linked] of scenarios) {
    const project = {id: 'fixture', validated_citations: []};
    const initialClick = await templateClick(script, project, initial);
    assert.equal(initialClick.requests.length, 1);
    assert.equal(JSON.parse(initialClick.requests[0].body).year, initial.year ?? null);
    project.validated_citations = [JSON.parse(initialClick.requests[0].body)];
    const nextClick = await templateClick(script, project, second);
    results.push({name, linked, ...nextClick});
    console.log(JSON.stringify(results.at(-1)));
  }
  assert.deepEqual(results.map(row => [row.blocked, row.requests.length]),
    scenarios.map(([, , , linked]) => [linked, linked ? 0 : 1]));
}
main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
