import pytest
from educhain.core.config import LLMConfig
from educhain.engines.qna_engine import QnAEngine
from unittest.mock import patch, MagicMock
from educhain.models.qna_models import (
    MCQList, ShortAnswerQuestionList, TrueFalseQuestionList,
    FillInBlankQuestionList, MCQListMath, VisualMCQList
)


class TestBasicQuestionGeneration:
    @pytest.fixture
    def engine(self):
        config = LLMConfig(
            model_name="mistral",
            base_url="http://localhost:11434",
            temperature=0.7
        )
        with patch('educhain.engines.qna_engine.QnAEngine._check_ollama_connection') as mock_check:
            mock_check.return_value = True
            return QnAEngine(config)

    @pytest.mark.parametrize("question_type,model,topic", [
        ("Multiple Choice", MCQList, "Python Programming"),
        ("Short Answer", ShortAnswerQuestionList, "World History"),
        ("True/False", TrueFalseQuestionList, "Science"),
        ("Fill in the Blank", FillInBlankQuestionList, "English Grammar")
    ])
    def test_generate_different_question_types(self, engine, question_type, model, topic):
        """Test generating different types of questions"""
        with patch('langchain_ollama.OllamaLLM.predict') as mock_predict:
            if question_type == "True/False":
                mock_response = """
                {
                    "questions": [
                        {
                            "question": "Python is a programming language?",
                            "answer": true,
                            "explanation": "Python is indeed a programming language"
                        },
                        {
                            "question": "Python was created in 2020?",
                            "answer": false,
                            "explanation": "Python was created in 1991"
                        }
                    ]
                }
                """
            elif question_type == "Fill in the Blank":
                mock_response = """
                {
                    "questions": [
                        {
                            "question": "The ___ is the capital of France.",
                            "answer": "Paris",
                            "explanation": "Paris is the capital of France",
                            "blank_word": "Paris"
                        },
                        {
                            "question": "Python was created by ___ van Rossum.",
                            "answer": "Guido",
                            "explanation": "Guido van Rossum created Python",
                            "blank_word": "Guido"
                        }
                    ]
                }
                """
            else:
                mock_response = """
                {
                    "questions": [
                        {
                            "question": "Test Question 1?",
                            "answer": "Test Answer 1",
                            "explanation": "Test Explanation 1",
                            "options": ["Option A", "Option B", "Option C", "Option D"]
                        },
                        {
                            "question": "Test Question 2?",
                            "answer": "Test Answer 2",
                            "explanation": "Test Explanation 2",
                            "options": ["Option A", "Option B", "Option C", "Option D"]
                        }
                    ]
                }
                """
            mock_predict.return_value = mock_response
            
            questions = engine.generate_questions(
                question_type=question_type,
                num=2,
                topic=topic
            )
            
            print(f"\n=== Generated {question_type} Questions for {topic} ===")
            print(questions)
            
            assert questions is not None
            assert len(questions.questions) == 2
            assert all(hasattr(q, 'question') for q in questions.questions)
            
            if question_type == "True/False":
                assert all(isinstance(q.answer, bool) for q in questions.questions)
            elif question_type == "Fill in the Blank":
                assert all(q.blank_word is not None for q in questions.questions)


class TestMathQuestionGeneration:
    @pytest.fixture
    def engine(self):
        config = LLMConfig(
            model_name="mistral",
            base_url="http://localhost:11434",
            temperature=0.7
        )
        with patch('educhain.engines.qna_engine.QnAEngine._check_ollama_connection') as mock_check:
            mock_check.return_value = True
            return QnAEngine(config)

    def test_generate_math_questions(self, engine):
        """Test generating math questions with computation"""
        with patch('langchain_ollama.OllamaLLM.predict') as mock_predict, \
             patch('langchain.chains.LLMMathChain.from_llm') as mock_math_chain:
            
            # Mock the math chain
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = {"answer": "3"}
            mock_math_chain.return_value = mock_chain
            
            mock_predict.return_value = """
            {
                "questions": [
                    {
                        "question": "Solve for x: 2x + 4 = 10",
                        "answer": "3",
                        "explanation": "Subtract 4 from both sides, then divide by 2",
                        "requires_math": true,
                        "options": ["1", "2", "3", "4"]
                    },
                    {
                        "question": "Calculate: 15% of 200",
                        "answer": "30",
                        "explanation": "Multiply 200 by 0.15",
                        "requires_math": true,
                        "options": ["20", "25", "30", "35"]
                    }
                ]
            }
            """
            
            questions = engine.generate_mcq_math(
                topic="Basic Algebra",
                num=2
            )
            
            print("\n=== Generated Math Questions ===")
            print(questions)
            
            assert questions is not None
            assert len(questions.questions) == 2
            assert all(q.requires_math for q in questions.questions)
            assert all(len(q.options) == 4 for q in questions.questions)
            
            # Verify that the math chain was called
            mock_chain.invoke.assert_called()


class TestSourceBasedQuestionGeneration:
    @pytest.fixture
    def engine(self):
        config = LLMConfig(
            model_name="mistral",
            base_url="http://localhost:11434",
            temperature=0.7
        )
        with patch('educhain.engines.qna_engine.QnAEngine._check_ollama_connection') as mock_check:
            mock_check.return_value = True
            return QnAEngine(config)

    @pytest.fixture
    def mock_content(self):
        return """
        The Python programming language was created by Guido van Rossum and was 
        released in 1991. Python is known for its simple syntax and readability. 
        It supports multiple programming paradigms, including procedural, 
        object-oriented, and functional programming.
        """

    def test_generate_questions_from_text(self, engine, mock_content):
        """Test generating questions from text content"""
        with patch.object(engine, '_load_data', return_value=mock_content), \
             patch('langchain_ollama.OllamaLLM.predict') as mock_predict:
            
            mock_predict.return_value = """
            {
                "questions": [
                    {
                        "question": "Who created Python?",
                        "answer": "Guido van Rossum",
                        "explanation": "Python was created by Guido van Rossum",
                        "options": ["Guido van Rossum", "James Gosling", "Bjarne Stroustrup", "Larry Wall"]
                    },
                    {
                        "question": "When was Python released?",
                        "answer": "1991",
                        "explanation": "Python was released in 1991",
                        "options": ["1989", "1990", "1991", "1992"]
                    }
                ]
            }
            """
            
            questions = engine.generate_questions_from_data(
                source=mock_content,
                source_type="text",
                num=2,
                question_type="Multiple Choice"
            )
            
            print("\n=== Generated Questions from Text ===")
            print(questions)
            
            assert questions is not None
            assert len(questions.questions) == 2

    def test_web_search_integration(self, engine):
        """Test generating questions with web search enabled"""
        mock_web_content = """
        Quantum computing is a type of computation that harnesses the power of quantum 
        mechanics. Unlike classical computers that use bits, quantum computers use 
        quantum bits or qubits. This allows them to perform certain calculations 
        exponentially faster than classical computers.
        """
        
        mock_firecrawl_response = {
            "success": True,
            "data": {
                "markdown": mock_web_content
            }
        }
        
        # Create a mock client with the scrape method
        mock_client = MagicMock()
        mock_client.scrape.return_value = mock_firecrawl_response
        
        # Patch the client creation instead of the initialization
        with patch.object(engine, 'firecrawl_client', mock_client), \
             patch('langchain_ollama.OllamaLLM.predict') as mock_predict:
            
            mock_predict.return_value = """
            {
                "questions": [
                    {
                        "question": "What is the fundamental unit of quantum computing?",
                        "answer": "Qubits",
                        "explanation": "Quantum computers use quantum bits or qubits instead of classical bits",
                        "options": ["Bits", "Qubits", "Bytes", "Neurons"]
                    }
                ]
            }
            """
            
            questions = engine.generate_questions(
                topic="Quantum Computing",
                num=1,
                web_search=True
            )
            
            assert questions is not None
            assert len(questions.questions) == 1
            # Check that web content was incorporated into either question or explanation
            assert any(
                "qubit" in q.question.lower() or 
                "qubit" in q.explanation.lower() or
                "qubit" in q.answer.lower()
                for q in questions.questions
            )

    def test_web_search_error_handling(self, engine):
        """Test handling of web search errors"""
        with patch.object(engine, '_get_web_context', return_value=""), \
             patch('langchain_ollama.OllamaLLM.predict') as mock_predict:
            
            mock_predict.return_value = """
            {
                "questions": [
                    {
                        "question": "Basic question without web content?",
                        "answer": "Basic answer",
                        "explanation": "Basic explanation",
                        "options": ["Option A", "Option B", "Option C", "Option D"]
                    }
                ]
            }
            """
            
            # Should still generate questions even if web search fails
            questions = engine.generate_questions(
                topic="Any Topic",
                num=1,
                web_search=True
            )
            
            assert questions is not None
            assert len(questions.questions) == 1

    def test_web_context_extraction(self, engine):
        """Test the web context extraction functionality"""
        mock_firecrawl_response = {
            "success": True,
            "data": {
                "markdown": "First source content\n\nSecond source content\n\nThird source content"
            }
        }
        
        # Create a mock client with the scrape method
        mock_client = MagicMock()
        mock_client.scrape.return_value = mock_firecrawl_response
        
        # Patch the client directly
        with patch.object(engine, 'firecrawl_client', mock_client):
            context = engine._get_web_context("test topic", max_results=3)
            
            assert context is not None
            assert "First source content" in context
            assert "Second source content" in context
            assert "Third source content" in context

    def test_web_search_custom_instructions(self, engine):
        """Test that web search properly modifies custom instructions"""
        mock_web_content = "Sample web content"
        
        with patch.object(engine, '_get_web_context', return_value=mock_web_content), \
             patch('langchain_ollama.OllamaLLM.predict') as mock_predict:
            
            mock_predict.return_value = """
            {
                "questions": [
                    {
                        "question": "Test question?",
                        "answer": "Test answer",
                        "explanation": "Test explanation",
                        "options": ["A", "B", "C", "D"]
                    }
                ]
            }
            """
            
            # Test with existing custom instructions
            questions = engine.generate_questions(
                topic="Test Topic",
                num=1,
                web_search=True,
                custom_instructions="Original instructions"
            )
            
            # Verify custom instructions were properly modified
            assert "Original instructions" in mock_predict.call_args[0][0]
            assert "web sources" in mock_predict.call_args[0][0].lower()
            assert "current" in mock_predict.call_args[0][0].lower()


class TestYouTubeQuestionGeneration:
    @pytest.fixture
    def engine(self):
        config = LLMConfig(
            model_name="mistral",
            base_url="http://localhost:11434",
            temperature=0.7
        )
        with patch('educhain.engines.qna_engine.QnAEngine._check_ollama_connection') as mock_check:
            mock_check.return_value = True
            return QnAEngine(config)

    @pytest.fixture
    def mock_transcript(self):
        return "This is a sample YouTube video transcript about Python programming."

    def test_generate_questions_from_youtube(self, engine, mock_transcript):
        """Test generating questions from YouTube content"""
        with patch.object(engine, '_extract_video_id', return_value="dummy_id"), \
             patch.object(engine, '_get_youtube_transcript', return_value=(mock_transcript, "en")), \
             patch('langchain_ollama.OllamaLLM.predict') as mock_predict:
            
            mock_predict.return_value = """
            {
                "questions": [
                    {
                        "question": "What is the main topic of the video?",
                        "answer": "Python programming",
                        "explanation": "The video discusses Python programming",
                        "options": ["Python programming", "Java programming", "C++ programming", "JavaScript programming"]
                    },
                    {
                        "question": "What type of content is this?",
                        "answer": "A YouTube video transcript",
                        "explanation": "This is a transcript from a YouTube video",
                        "options": ["Blog post", "Book excerpt", "YouTube video transcript", "Magazine article"]
                    }
                ]
            }
            """
            
            questions = engine.generate_questions_from_youtube(
                url="https://youtube.com/watch?v=dummy",
                num=2
            )
            
            print("\n=== Generated Questions from YouTube ===")
            print(questions)
            
            assert questions is not None
            assert len(questions.questions) == 2 