"""Local scripted chat path: no OpenRouter and no GPT-SoVITS."""
import importlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class LocalReplyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        previous_directory = os.getcwd()
        os.chdir(self.directory.name)
        self.addCleanup(os.chdir, previous_directory)
        backend = str(Path(__file__).resolve().parents[1])
        sys.path.insert(0, backend)
        self.addCleanup(sys.path.remove, backend)
        modules = patch.dict(sys.modules, {
            'llm': SimpleNamespace(get_llm=lambda *args: None, reset_llm=lambda: None),
            'tts': SimpleNamespace(
                streamVoiceChunks=lambda text: iter(()),
                tts_available=lambda: False,
            ),
        })
        modules.start()
        self.addCleanup(modules.stop)
        for name in ('api', 'chat', 'memory', 'chat_interactions', 'local_replies'):
            sys.modules.pop(name, None)
        os.environ.pop('AMADEUS_NO_AI', None)
        self.api = importlib.import_module('api')
        self.chat = importlib.import_module('chat')
        self.memory = importlib.import_module('memory')
        self.local_replies = importlib.import_module('local_replies')
        self.client = self.api.application.test_client()

    def test_substring_hi_does_not_match_this(self):
        english, _japanese = self.local_replies.scripted_reply('Look at this file.')
        self.assertIn('Stored.', english)
        self.assertNotIn('Hello.', english)

    def test_special_interaction_rewrites_audio_url(self):
        response = self.client.post('/doSpecialInteraction', json={'interaction_value': 2})
        self.assertEqual(response.status_code, 200)
        audio_url = response.json['audio_url']
        self.assertTrue(audio_url.startswith('/reaction_audio/maho_'))
        audio = self.client.get(audio_url)
        self.assertEqual(audio.status_code, 200)
        self.assertTrue(audio.data.startswith(b'RIFF'))
        self.assertGreater(len(audio.data), 1000)

    def test_greeting_and_status_without_key(self):
        status = self.client.get('/api_key_status')
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json['configured'], False)
        self.assertEqual(status.json['no_ai'], True)

        response = self.client.post('/', json={'user_input': 'hello'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Local Amadeus is running', response.json['response'])
        self.assertNotIn('speech_id', response.json)

        memory = self.memory.load_memory_raw()
        self.assertEqual(memory[0]['role'], 'user')
        self.assertEqual(memory[0]['content'], 'hello')
        self.assertEqual(memory[1]['role'], 'assistant')
        self.assertIn('Local Amadeus is running', memory[1]['content'])

    def test_forced_no_ai_keeps_scripted_replies_with_a_key(self):
        os.environ['AMADEUS_NO_AI'] = '1'
        self.addCleanup(os.environ.pop, 'AMADEUS_NO_AI', None)
        self.chat.setKey('sk-or-v1-test')
        self.assertTrue(self.chat.has_api_key())
        self.assertTrue(self.chat.uses_local_replies())
        pack = self.chat.getOutputPacked('who are you')
        self.assertIn('Makise Kurisu', pack.assistant_reply_ENG)

    def test_key_enables_llm_path_when_no_ai_is_unset(self):
        captured = []
        reply = self.chat.AmadeusPack(assistant_reply_ENG='From the model', assistant_reply_JPS='モデル')
        fake = SimpleNamespace(with_structured_output=lambda *a, **k:
                               SimpleNamespace(invoke=lambda messages: captured.extend(messages) or reply))
        self.chat.setKey('sk-or-v1-test')
        self.assertFalse(self.chat.uses_local_replies())
        with patch.object(self.chat, 'get_llm', return_value=fake):
            pack = self.chat.getOutputPacked('hello')
        self.assertEqual(pack.assistant_reply_ENG, 'From the model')
        self.assertTrue(captured)


if __name__ == '__main__':
    unittest.main()
