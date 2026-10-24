import json
import sys
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import Chatbot
from app import Handler, ThreadingHTTPServer


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = Chatbot()

    def test_representative_phrasings(self):
        cases = {
            'Please explain how to submit an application': 'admission_process',
            'What are the eligibility rules?': 'admission_eligibility',
            'What documents must I upload?': 'admission_documents',
            'When is the last admission date?': 'admission_deadline',
            'Show me available degree programs': 'courses_offered',
            'How many years will I study?': 'course_duration',
            'Where is the curriculum?': 'course_syllabus',
            'Tell me the yearly tuition cost': 'tuition_fees',
            'Can I split my fee payment?': 'fee_payment',
            'Do you offer financial aid to students?': 'scholarships',
            'How can I find a summer internship?': 'internship_support',
            'Are internship credits required?': 'internship_requirement',
            'Will my internship pay a stipend?': 'internship_stipend',
            'How can I register for campus recruitment?': 'placement_process',
            'Which employers recruit students?': 'placement_companies',
            'Tell me the median placement salary': 'placement_statistics',
            'Can I stay in a hostel?': 'hostel',
            'HELLO!!!': 'greeting',
            'Thank you': 'thanks',
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertEqual(self.bot.predict(question)['intent'], expected)

    def test_unknown_questions(self):
        for question in ['Tell me a joke', 'What is the weather tomorrow?',
                         'Who won the cricket match?', 'asdfgh qwerty', '', '!!!',
                         'Write a recipe for chocolate cake']:
            with self.subTest(question=question):
                self.assertEqual(self.bot.predict(question)['intent'], 'fallback')

    def test_dataset_integrity(self):
        ids = [item['id'] for item in self.bot.data['intents']]
        self.assertEqual(len(ids), len(set(ids)))
        questions = [q.lower() for q, _ in self.bot.samples]
        self.assertEqual(len(questions), len(set(questions)))
        for item in self.bot.intents.values():
            self.assertTrue(item['answer'])
            self.assertTrue(item['source'])
            self.assertGreaterEqual(len(item['questions']), 5)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, payload):
        req = Request(self.base + '/api/chat', data=payload, headers={'Content-Type': 'application/json'})
        return urlopen(req, timeout=5)

    def test_chat_response(self):
        with self.post(json.dumps({'message': 'What are the tuition fees?'}).encode()) as response:
            data = json.load(response)
        self.assertEqual(data['intent'], 'tuition_fees')
        self.assertIn('No verified fee amounts', data['answer'])

    def test_bad_requests(self):
        for payload in [b'not json', b'[]', b'{}', b'{"message":42}', b'{"message":" "}',
                        json.dumps({'message': 'a' * 501}).encode()]:
            with self.subTest(payload=payload[:40]):
                with self.assertRaises(HTTPError) as context:
                    self.post(payload)
                self.assertEqual(context.exception.code, 400)

    def test_size_limit(self):
        with self.assertRaises(HTTPError) as context:
            self.post(b'x' * 8193)
        self.assertEqual(context.exception.code, 413)

    def test_static_assets_and_info(self):
        for path, mime in [('/', 'text/html'), ('/style.css', 'text/css'),
                           ('/chat.js', 'text/javascript'), ('/api/info', 'application/json')]:
            with self.subTest(path=path):
                with urlopen(self.base + path, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn(mime, response.headers['Content-Type'])
                    self.assertTrue(response.read())

    def test_no_arbitrary_file_access(self):
        for path in ['/model.py', '/data/faqs.json', '/../app.py']:
            with self.subTest(path=path):
                with self.assertRaises(HTTPError) as context:
                    urlopen(self.base + path, timeout=5)
                self.assertEqual(context.exception.code, 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
