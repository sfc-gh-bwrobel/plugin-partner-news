"""Regression checks for digest grouping and content preservation."""
import re
import json
from urllib.parse import parse_qs, urlparse
import unittest
from collections import Counter
from html.parser import HTMLParser

from build_site import ROOT, blocks, inline, parse_digest, render, source_directory


class Page(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.ids = []
        self.links = []
        self.fragments = []
        self.text = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a':
            href = attrs.get('href', '')
            (self.fragments if href.startswith('#') else self.links).append(href)

    def handle_data(self, data):
        self.text.append(data)


class DigestTests(unittest.TestCase):
    def test_archive_content_and_links_preserved(self):
        for file in sorted((ROOT / 'digests/capgemini').glob('digest-*.md')):
            with self.subTest(file=file.name):
                markdown = file.read_text()
                page = Page(render(markdown, 'week'))
                original_links = Page(inline(markdown)).links
                self.assertEqual(Counter(original_links), Counter(page.links))
                self.assertEqual(len(page.ids), len(set(page.ids)))
                self.assertTrue(all(fragment[1:] in page.ids for fragment in page.fragments))
                text = ' '.join(' '.join(page.text).split())
                _, metadata, sections = parse_digest(markdown)
                for section in sections:
                    for story in section['stories']:
                        title = re.sub(r'^Client story:\s*', '', story['title'])
                        self.assertIn(title, text)
                        for line in story['lines']:
                            if not line.strip():
                                continue
                            plain = re.sub(r'^\s*-\s+', '', line)
                            expected = ' '.join(' '.join(Page(inline(plain)).text).split())
                            self.assertIn(expected, text)

    def test_empty_sections_are_compact_and_absent_from_navigation(self):
        markdown = '# Test\nStatus: DRAFT\n## Snowflake mentions\nNone this week.\n## Top stories\n### News\nA fact.'
        markup = render(markdown, 'week')
        self.assertNotIn('href="#week-snowflake', markup)
        self.assertNotIn('<h4>Snowflake mentions', markup)
        self.assertIn('<p class="coverage">', markup)
        self.assertIn('No updates found:', markup)
        self.assertIn('None this week.', markup)

    def test_client_stories_grouped_without_losing_sources_or_suggestions(self):
        markdown = '# Test\n## Top stories\n### 1. News\nA fact.\n### 2. Client story: Client\nOct 1 | Public\nDelivery.\n- Why it matters: Context.\n- Source: [Source](https://example.com/)'
        markup = render(markdown, 'week')
        news = markup.split('<section class="news"')[1].split('</section>')[0]
        clients = markup.split('<section class="clients"')[1].split('</section>')[0]
        self.assertNotIn('<h4>Client', news)
        self.assertIn('<h4>Client</h4>', clients)
        self.assertIn('Context.', clients)
        self.assertIn('https://example.com/', clients)
        self.assertIn('<details class="angle">', clients)
        self.assertNotIn('<details class="angle" open', clients)

    def test_metadata_is_disclosed_but_not_prominent(self):
        markdown = '# Test\nSources: 12 raw | Judged: `file.json`\nSuggestions, not facts.\n## Top stories\n### News\nFact.'
        markup = render(markdown, 'week')
        visible_header = markup.split('</header>')[0]
        self.assertNotIn('Draft', visible_header)
        self.assertNotIn('class="status"', markup)
        self.assertNotIn('12 raw', visible_header)
        self.assertNotIn('file.json', visible_header)
        self.assertNotIn('Suggestions, not facts.', visible_header)
        self.assertIn('file.json', markup.split('<details class="about">')[1])

    def test_source_html_and_unsafe_links_are_not_executable(self):
        self.assertNotIn('<script>', blocks(['<script>alert(1)</script>']))
        self.assertNotIn('href="javascript:', inline('[bad](javascript:alert)'))
        self.assertIn('rel="noopener noreferrer"', inline('[ok](https://example.com/)'))

    def test_source_directory_covers_current_config_and_is_collapsed(self):
        cfg = json.loads((ROOT / 'partners/capgemini.json').read_text())
        markup = source_directory(cfg)
        page = Page(markup)
        self.assertIn('<details class="about source-directory" id="monitored-sources">', markup)
        self.assertNotRegex(markup, r'<details[^>]*\sopen(?:\s|=|>)')
        self.assertIn('not a record of successful checks', markup)
        self.assertIn('Manual checks, not automated', markup)
        for feed in cfg['feeds']:
            self.assertIn(feed['url'], page.links)
        searches = [parse_qs(urlparse(url).query) for url in page.links
                    if urlparse(url).netloc == 'news.google.com']
        google = cfg['google_news']
        self.assertEqual(len(searches), len(google['queries']) * len(google['locales']))
        for query in google['queries']:
            for locale in google['locales']:
                self.assertIn({key: [value] for key, value in {'q': query['q'], **locale}.items()}, searches)
        for manual in cfg['manual_checks']:
            self.assertIn(re.search(r'https?://\S+', manual)[0], page.links)

    def test_source_directory_escapes_configuration(self):
        cfg = {'feeds': [{'id': '<script>bad</script>', 'url': 'javascript:alert'}],
               'google_news': {'queries': [], 'locales': []}}
        markup = source_directory(cfg)
        self.assertNotIn('<script>', markup)
        self.assertNotIn('href="javascript:', markup)

    def test_more_news_position_and_plain_groups(self):
        markdown = ('# Test\n## Top stories\n### Client story: Acme\nDelivery.\n'
                    '## More news\n### AI, data & technology\n'
                    '- 2026-10-10 | A factual sentence. [Publisher](https://example.com/)\n'
                    '### Research & reports\n\n## Coming up\n- October 30: Earnings.')
        markup = render(markdown, 'week')
        self.assertLess(markup.index('class="clients"'), markup.index('class="more-news"'))
        self.assertLess(markup.index('class="more-news"'), markup.index('class="about"'))
        more = markup.split('class="more-news"')[1].split('</section>')[0]
        self.assertIn('<ul><li>', more)
        self.assertNotIn('Research &amp; reports', more)
        self.assertNotIn('class="story"', more)
        self.assertNotIn('Team take', more)
        self.assertNotIn('remaining-news', more)
        self.assertNotIn('Earnings', more)
        self.assertIn('href="#week-more"', markup)

    def test_more_news_limit_grouping_and_date_order(self):
        markdown = '# Test\n## More news\n### AI, data & technology\n'
        markdown += '\n'.join(f'- 2026-10-{day:02} | Item {day}. [Source](https://example.com/{day})'
                              for day in range(1, 15))
        markdown += '\n### Business & partnerships\n- 2026-09-30 | Older partnership.'
        markup = render(markdown, 'week')
        preview, remaining = markup.split('<details class="remaining-news">')
        self.assertEqual(preview.count('<li>'), 12)
        self.assertEqual(remaining.count('<li>'), 3)
        self.assertIn('Show remaining news (3)', remaining)
        self.assertNotIn('<details class="remaining-news" open', markup)
        self.assertIn('AI, data &amp; technology (continued)', remaining)
        self.assertIn('<h4>Business &amp; partnerships</h4>', remaining)
        self.assertLess(preview.index('Item 14'), preview.index('Item 13'))
        self.assertLess(remaining.index('Item 2'), remaining.index('Item 1'))
        self.assertEqual(len(Page(markup).links), 14)

    def test_more_news_threshold_and_legacy_also_noted(self):
        for count in (0, 1, 12, 13):
            markdown = '# Test\n## More news\n### People & organisation\n'
            markdown += '\n'.join(f'- 2026-10-16 | Update {index}.' for index in range(count))
            markup = render(markdown, 'week')
            self.assertEqual('class="remaining-news"' in markup, count > 12)
            self.assertEqual('class="more-news"' in markup, count > 0)
        markup = render('# Test\n## Also noted\n- A fact. [Source](https://example.com/)', 'week')
        self.assertIn('class="more-news"', markup)
        self.assertNotIn('class="briefs"', markup)
        self.assertNotIn('Also noted', markup)

    def test_archived_more_news_has_dates_links_and_no_duplicates(self):
        for file in (ROOT / 'digests/capgemini').glob('digest-*.md'):
            markdown = file.read_text()
            _, _, sections = parse_digest(markdown)
            more = next(section for section in sections if section['title'] == 'More news')
            other_links = [url for section in sections if section is not more
                           for url in Page(blocks(section['lines']) + ''.join(
                               blocks(story['lines']) for story in section['stories'])).links]
            links = []
            for group in more['stories']:
                items = [line for line in group['lines'] if line.strip()]
                self.assertTrue(items)
                self.assertEqual(items, sorted(items, reverse=True))
                for item in items:
                    self.assertRegex(item, r'^- \d{4}-\d{2}-\d{2} \| ')
                    self.assertNotRegex(item, r'Why it matters|Follow-up:')
                    urls = Page(inline(item)).links
                    self.assertTrue(urls)
                    self.assertFalse(set(urls) & set(other_links))
                    links.extend(urls)
            self.assertEqual(len(links), len(set(links)))

    def test_main_news_has_two_substantive_paragraphs(self):
        for file in (ROOT / 'digests/capgemini').glob('digest-*.md'):
            _, _, sections = parse_digest(file.read_text())
            for section in sections:
                if section['title'] != 'Top stories':
                    continue
                for story in section['stories']:
                    if story['title'].startswith('Client story:'):
                        continue
                    with self.subTest(file=file.name, story=story['title']):
                        body = '\n'.join(line for line in story['lines']
                                         if not line.startswith('- ') and '|' not in line).strip()
                        paragraphs = re.split(r'\n\s*\n', body)
                        self.assertEqual(len(paragraphs), 2)
                        self.assertGreaterEqual(len(body.split()), 80)
                        self.assertLessEqual(len(body.split()), 120)
                        from build_site import story_html
                        markup = story_html(story)
                        # Source and metadata are separate paragraphs; editorial notes remain collapsed.
                        self.assertEqual(markup.split('<details')[0].count('<p>'), 2)
                        self.assertNotIn('<details class="angle" open', markup)

    def test_history_caps_live_editions_and_keeps_downloads(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from build_site import build_page
        with TemporaryDirectory() as directory:
            files = []
            archive = {'editions': {}}
            for day in range(1, 15):
                file = Path(directory) / f'digest-2026-10-{day:02}.md'
                file.write_text(f'# Week {day}\n## Top stories\n### News\nUnique story {day}.')
                files.append(file)
                archive['editions'][f'2026-10-{day:02}'] = f'file_{day}'
            files.reverse()
            markup = build_page(files, {'name': 'Test'}, 'test', archive)
            self.assertEqual(markup.count('<option '), 12)
            self.assertEqual(markup.count('<section class="digest"'), 12)
            self.assertIn('value="w2026-10-14" selected', markup)
            self.assertNotIn('Unique story 1.', markup)
            self.assertNotIn('Unique story 2.', markup)
            self.assertEqual(markup.count('Download HTML'), 26)  # 12 current + 14 history
            history = markup.split('id="history"')[1].split('</section>')[0]
            self.assertIn('file_1/view', history)
            self.assertIn('<h4>2026</h4>', history)
            self.assertLess(history.index('file_14/view'), history.index('file_1/view'))
            page = Page(markup)
            self.assertEqual(len(page.ids), len(set(page.ids)))
            self.assertTrue(all(fragment[1:] in page.ids for fragment in page.fragments))
            standalone = build_page([files[0]], {'name': 'Test'}, 'test', {}, standalone=True)
            self.assertEqual(standalone.count('<section class="digest"'), 1)
            self.assertNotIn('id="history"', standalone)
            self.assertNotIn('(latest)', standalone)
            self.assertNotIn('__HISTORY', standalone)
            self.assertIn('Created and maintained by Bart Wrobel', standalone)

    def test_snapshot_preservation_and_missing_archive_guard(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from unittest.mock import patch
        import build_site
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'partners').mkdir()
            (root / 'partners/test.json').write_text('{"name":"Test"}')
            digests = root / 'digests/test'
            digests.mkdir(parents=True)
            for day in range(1, 14):
                (digests / f'digest-2026-10-{day:02}.md').write_text(f'# Week {day}\n## Top stories\n### News\nFact.')
            with patch.object(build_site, 'ROOT', root), patch('sys.argv', ['build_site.py', 'test']):
                with self.assertRaisesRegex(SystemExit, '2026-10-01'):
                    build_site.main()
                self.assertFalse((root / 'site/test-news.html').exists())
                snapshots = list((root / 'site/archive/test').glob('*.html'))
                self.assertEqual(len(snapshots), 13)
                original = snapshots[0].read_bytes()
                (digests / 'archive.json').write_text('{"editions":{"2026-10-01":"drive_file_1"}}')
                build_site.main()
                self.assertEqual(snapshots[0].read_bytes(), original)
                self.assertTrue((root / 'site/test-news.html').exists())

    def test_backfill_decisions_cover_every_collected_candidate(self):
        for day in ('2026-09-27', '2026-10-04'):
            folder = ROOT / 'raw/capgemini'
            raw = json.loads((folder / f'{day}.json').read_text())['items']
            judged = json.loads((folder / f'{day}.judged.json').read_text())['items']
            self.assertEqual(sorted(item['id'] for item in raw), sorted(item['id'] for item in judged))
            self.assertTrue(all(item.get('reason') for item in judged))
            leads = [item for item in judged if item.get('keep') and item.get('lead')]
            self.assertEqual(len(leads), len({item['cluster'] for item in leads}))
            markdown = (ROOT / f'digests/capgemini/digest-{day}.md').read_text()
            for item in leads:
                self.assertIn(item['resolved_link'], markdown)

    def test_corrected_weeks_are_consecutive_and_dates_fit(self):
        from datetime import date, timedelta
        from build_site import edition_day
        folder = ROOT / 'digests/capgemini'
        archive = json.loads((folder / 'archive.json').read_text())
        active = sorted(file for file in folder.glob('digest-*.md')
                        if edition_day(file) not in archive.get('superseded', []))
        self.assertGreaterEqual(len(active), 4)
        previous = None
        for file in active:
            end = date.fromisoformat(edition_day(file))
            self.assertEqual(end.weekday(), 6)
            if previous:
                self.assertEqual(end - previous, timedelta(days=7))
            previous = end
            _, _, sections = parse_digest(file.read_text())
            for section in sections:
                if section['title'] in ('Manual checks', 'Coming up'):
                    continue
                lines = section['lines'] + [line for story in section['stories'] for line in story['lines']]
                for line in lines:
                    match = re.match(r'^(?:- )?(\d{4}-\d{2}-\d{2}) \|', line)
                    if match:
                        self.assertTrue(end - timedelta(days=6) <= date.fromisoformat(match[1]) <= end)
        for day in archive.get('pending', []):
            self.assertFalse((ROOT / f'site/archive/capgemini/capgemini-news-{day}.html').exists())

    def test_pending_and_superseded_editions_are_not_snapshotted(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from unittest.mock import patch
        import build_site
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'partners').mkdir()
            (root / 'partners/test.json').write_text('{"name":"Test"}')
            folder = root / 'digests/test'
            folder.mkdir(parents=True)
            for day in ('2020-01-05', '2020-01-12'):
                (folder / f'digest-{day}.md').write_text('# Test\nEdition note: Coverage incomplete.\n## Top stories\n### News\nFact.')
            (folder / 'archive.json').write_text(json.dumps({'editions': {'2020-01-05': 'old_file'},
                'superseded': ['2020-01-05'], 'pending': ['2020-01-12']}))
            with patch.object(build_site, 'ROOT', root), patch('sys.argv', ['build_site.py', 'test']):
                build_site.main()
            markup = (root / 'site/test-news.html').read_text()
            self.assertEqual(markup.count('<option '), 1)
            self.assertIn('class="edition-note">Coverage incomplete.', markup)
            self.assertIn('Earlier versions', markup)
            self.assertIn('old_file/view', markup)
            self.assertFalse(list((root / 'site/archive/test').glob('*.html')))

    def test_history_rejects_unsafe_file_ids(self):
        from build_site import archive_links
        with self.assertRaises(ValueError):
            archive_links('2026-10-16', {'editions': {'2026-10-16': 'bad" onclick="alert(1)'}})

    def test_all_empty_and_explicit_client_section(self):
        markup = render('# Empty\n## Snowflake mentions\nNone this week.', 'empty')
        self.assertIn('No updates found', markup)
        markup = render('# Test\n## Client stories\n### Client\nA delivery.', 'client')
        self.assertIn('id="client-clients"', markup)
        self.assertNotIn('id="client-news"', markup)


if __name__ == '__main__':
    unittest.main()
