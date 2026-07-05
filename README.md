# manosamvada
My project is Manosamvada, which means Dialogue of the Mind. It is an AI-based mental health chatbot developed using Python, Flask, MySQL, JavaScript, and the SambaNova AI API. The main goal of the project is to provide an empathetic conversational support system for users facing stress, anxiety, or emotional distress. 
The system allows users to register/login securely using OTP-based email verification and hashed passwords. Once logged in, users can chat with the AI through a real-time web interface.

The core functionality is based on two layers: emotion detection and LLM-based response generation. First, the backend analyzes the user’s message using a rule-based emotion detection module to classify emotions like happy, sad, angry, neutral, or crisis. Then, based on the detected emotion, the system dynamically adjusts the response tone before sending the message to the Meta-Llama-3.1-8B-Instruct model through the SambaNova API using the OpenAI Python SDK.

A key feature of the project is the crisis detection module. The system checks messages against a database-driven list of crisis keywords such as self-harm or suicide-related phrases. If detected, the chatbot immediately provides supportive responses and mental health helpline information.

The backend is built using Flask and follows a three-tier architecture with frontend, application layer, and MySQL database layer. The database stores users, chat history, sessions, crisis keywords, and response templates in normalized tables designed in 3NF.

The project also includes features like persistent chat history, AI-generated session topics, analytics dashboards for users and admins, session search, CSV export, and guest access mode.

One limitation of the current system is that the emotion detection is rule-based, so it may not fully understand sarcasm or indirect emotions. As a future enhancement, we plan to integrate transformer-based NLP models like BERT for more accurate emotion understanding.”
