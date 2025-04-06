from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Gemini API setup
genai.configure(api_key="AIzaSyC7KFA5zdbJkg05KCnFbmxKLIwwc33-9yw")  # Replace with your real API key
model = genai.GenerativeModel("gemini-1.5-pro")

# Dark-themed HTML frontend
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>GenAI Financial Assistant</title>
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet" />
  <style>
    body {
      background-color: #111827;
    }
    .prose h3, .prose strong {
      color: #fff;
    }
    .prose ul li::marker {
      color: #60a5fa;
    }
  </style>
</head>
<body class="flex flex-col min-h-screen font-sans text-white">
  <header class="bg-gray-900 shadow p-4">
    <h1 class="text-2xl font-bold text-center text-blue-400">💬 GenAI Financial Assistant</h1>
  </header>

  <main class="flex-1 flex flex-col items-center px-4 py-6 overflow-y-auto">
    <div id="chat-box" class="w-full max-w-2xl space-y-4 overflow-y-auto">
      <!-- Chat messages appear here -->
    </div>
  </main>

  <form id="chat-form" class="w-full max-w-2xl mx-auto flex items-center gap-2 p-4 bg-gray-900 border-t border-gray-800">
    <input
      type="text"
      name="query"
      id="query"
      placeholder="Ask your finance question..."
      class="flex-1 border border-gray-700 bg-gray-800 text-white rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
      required
    />
    <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-full transition">
      Ask
    </button>
  </form>

  <script>
    const form = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const input = document.getElementById('query');
      const userMessage = input.value.trim();
      if (!userMessage) return;

      appendMessage('user', userMessage);
      input.value = '';

      appendMessage('bot', `<span class="text-gray-400 italic">Typing...</span>`);

      try {
        const res = await fetch('/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: userMessage }),
        });

        const data = await res.json();
        chatBox.lastChild.remove(); // Remove "typing..."
        appendMessage('bot', data.response);
      } catch (err) {
        chatBox.lastChild.remove();
        appendMessage('bot', '⚠️ Something went wrong. Please try again.');
        console.error(err);
      }
    });

    function appendMessage(sender, message) {
      const wrapper = document.createElement('div');
      wrapper.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`;

      const bubble = document.createElement('div');
      bubble.className = `p-4 rounded-2xl max-w-xl shadow text-base ${
        sender === 'user'
          ? 'bg-blue-600 text-white'
          : 'bg-gray-800 text-white border border-gray-700 prose'
      }`;

      bubble.innerHTML = message;
      wrapper.appendChild(bubble);
      chatBox.appendChild(wrapper);
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  </script>
</body>
</html>
"""

# Route: Home
@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

# Route: Ask
@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        query = data.get("query", "")

        if not query.strip():
            return jsonify({"response": "⚠️ Please enter a question."})

        # Filter: Only allow finance-related questions
        if not any(keyword in query.lower() for keyword in [
            "finance", "investment", "stock", "mutual fund", "savings", "bank",
            "portfolio", "money", "financial", "debt", "equity", "interest", "risk"
        ]):
            return jsonify({
                "response": "⚠️ This assistant only responds to finance and investment-related queries. Please ask something in that domain."
            })

        # Use Gemini chat model
        chat = model.start_chat(history=[])
        response = chat.send_message(query)

        content = response.text if response and response.text else None
        if not content:
            return jsonify({"response": "🤖 Gemini returned an empty response. Please try rephrasing your question."})

        formatted = format_response(content)
        return jsonify({"response": formatted})

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"response": "❌ Something went wrong while generating the response."})

# Format Gemini response to HTML
def format_response(text):
    lines = text.strip().split("\n")
    html = []
    summary_added = False
    in_list = False

    for line in lines:
        if not summary_added and line.strip():
            html.append(f"<div class='mb-2'><span class='text-blue-400 font-semibold'>📝 Summary:</span><br>{line.strip()}</div>")
            summary_added = True
        elif line.strip().startswith("-") or line.strip().startswith("*"):
            if not in_list:
                html.append("<ul class='list-disc pl-5 space-y-1'>")
                in_list = True
            html.append(f"<li>{line.strip()[1:].strip()}</li>")
        elif line.strip() == "":
            if in_list:
                html.append("</ul>")
                in_list = False
        else:
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<p>{line.strip()}</p>")

    if in_list:
        html.append("</ul>")

    # Add disclaimer
    html.append("""
    <div class='mt-4 text-sm text-gray-400'>
      ⚠️ <strong>Disclaimer:</strong> This is for educational purposes only and does not constitute financial advice. Please consult a SEBI-registered advisor before making investment decisions.
    </div>
    """)
    return "".join(html)

# Run
if __name__ == "__main__":
    app.run(debug=True)
