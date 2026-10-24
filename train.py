"""Export the TF-IDF model for inspection. Runtime rebuilds from the FAQ source.

The generated JSON is useful for teaching and inspection; editing data/faqs.json and restarting remains the source-of-truth workflow.
"""
from model import Chatbot, ROOT

if __name__ == '__main__':
    bot = Chatbot()
    target = ROOT / 'model.json'
    bot.export(target)
    print(f'Trained on {len(bot.samples)} questions across {len(bot.intents)} intents.')
    print(f'Model saved to {target}')
