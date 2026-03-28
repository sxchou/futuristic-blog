import pytest
from app.utils.helpers import (
    levenshtein_distance,
    calculate_similarity_score,
    find_similar_slug,
    generate_slug_with_fallback,
    generate_slug,
    generate_unique_slug
)


class TestLevenshteinDistance:
    def test_identical_strings(self):
        assert levenshtein_distance("hello", "hello") == 0
    
    def test_empty_string(self):
        assert levenshtein_distance("", "hello") == 5
        assert levenshtein_distance("hello", "") == 5
    
    def test_single_character_difference(self):
        assert levenshtein_distance("hello", "hallo") == 1
        assert levenshtein_distance("hello", "hell") == 1
    
    def test_complete_different_strings(self):
        assert levenshtein_distance("abc", "xyz") == 3
    
    def test_case_sensitivity(self):
        assert levenshtein_distance("Hello", "hello") == 1


class TestCalculateSimilarityScore:
    def test_identical_strings(self):
        score = calculate_similarity_score("hello-world", "hello-world")
        assert score == 1.0
    
    def test_empty_strings(self):
        assert calculate_similarity_score("", "hello") == 0.0
        assert calculate_similarity_score("hello", "") == 0.0
    
    def test_substring_match(self):
        score = calculate_similarity_score("hello", "hello-world")
        assert score >= 0.8
    
    def test_reverse_substring_match(self):
        score = calculate_similarity_score("hello-world", "hello")
        assert score >= 0.7
    
    def test_word_overlap(self):
        score = calculate_similarity_score("hello-world-test", "hello-world-demo")
        assert score >= 0.5
    
    def test_no_similarity(self):
        score = calculate_similarity_score("abc", "xyz")
        assert score < 0.5
    
    def test_partial_match(self):
        score = calculate_similarity_score("regex", "regular-expression")
        assert score >= 0.1


class TestFindSimilarSlug:
    def test_exact_prefix_match(self):
        existing = ["hello-world", "hello-world-2", "test-slug"]
        result = find_similar_slug("hello", existing)
        assert result == "hello-world"
    
    def test_no_match_below_threshold(self):
        existing = ["completely-different", "another-slug"]
        result = find_similar_slug("hello-world", existing, threshold=0.8)
        assert result is None
    
    def test_match_above_threshold(self):
        existing = ["hello-world-test", "another-slug"]
        result = find_similar_slug("hello-world", existing, threshold=0.5)
        assert result == "hello-world-test"
    
    def test_empty_input(self):
        existing = ["hello-world"]
        result = find_similar_slug("", existing)
        assert result is None
    
    def test_empty_existing_list(self):
        result = find_similar_slug("hello-world", [])
        assert result is None
    
    def test_best_match_selection(self):
        existing = ["hello-planet", "hello-world-test", "hello-earth"]
        result = find_similar_slug("hello-world", existing, threshold=0.5)
        assert result is not None


class TestGenerateSlugWithFallback:
    def test_exact_match(self):
        existing = ["hello-world", "test-slug"]
        result = generate_slug_with_fallback("Hello World", existing)
        assert result['slug'] == "hello-world"
        assert result['source'] == "exact_match"
        assert result['similarity_score'] == 1.0
    
    def test_similar_match(self):
        existing = ["hello-world-test", "another-slug"]
        result = generate_slug_with_fallback("Hello World", existing, similarity_threshold=0.5)
        assert result['source'] == "similar_match"
        assert result['similarity_score'] >= 0.5
    
    def test_generate_new_slug(self):
        existing = ["completely-different", "another-slug"]
        result = generate_slug_with_fallback("Hello World", existing, similarity_threshold=0.9)
        assert result['source'] == "generated"
        assert result['slug'] == "hello-world"
    
    def test_empty_input(self):
        existing = ["hello-world"]
        result = generate_slug_with_fallback("", existing)
        assert result['slug'] == "untitled"
        assert result['source'] == "default"
    
    def test_empty_existing_list(self):
        result = generate_slug_with_fallback("Hello World", [])
        assert result['slug'] == "hello-world"
        assert result['source'] == "generated"


class TestGenerateSlug:
    def test_english_text(self):
        slug = generate_slug("Hello World")
        assert slug == "hello-world"
    
    def test_special_characters(self):
        slug = generate_slug("Hello! World? #Test")
        assert slug == "hello-world-test"
    
    def test_multiple_spaces(self):
        slug = generate_slug("Hello    World")
        assert slug == "hello-world"
    
    def test_chinese_text(self):
        slug = generate_slug("你好世界")
        assert slug == "ni-hao-shi-jie"
    
    def test_mixed_text(self):
        slug = generate_slug("Hello 世界")
        assert "hello" in slug
    
    def test_empty_string(self):
        slug = generate_slug("")
        assert slug == ""
    
    def test_max_length(self):
        long_text = "a" * 200
        slug = generate_slug(long_text, max_length=50)
        assert len(slug) <= 50


class TestGenerateUniqueSlug:
    def test_unique_slug(self):
        existing = ["hello-world", "test-slug"]
        result = generate_unique_slug("new-slug", existing)
        assert result == "new-slug"
    
    def test_duplicate_slug(self):
        existing = ["hello-world", "test-slug"]
        result = generate_unique_slug("hello-world", existing)
        assert result == "hello-world-1"
    
    def test_multiple_duplicates(self):
        existing = ["hello-world", "hello-world-1", "hello-world-2"]
        result = generate_unique_slug("hello-world", existing)
        assert result == "hello-world-3"
    
    def test_empty_base_slug(self):
        existing = ["test-slug"]
        result = generate_unique_slug("", existing)
        assert result == "untitled"


class TestIncompleteTitleScenarios:
    def test_partial_title_prefix_match(self):
        existing = ["regular-expression-tutorial", "regex-basics"]
        result = generate_slug_with_fallback("regular", existing, similarity_threshold=0.5)
        assert result['matched_slug'] == "regular-expression-tutorial"
    
    def test_partial_title_word_overlap(self):
        existing = ["javascript-tutorial", "python-guide"]
        result = generate_slug_with_fallback("javascript", existing, similarity_threshold=0.5)
        assert result['matched_slug'] == "javascript-tutorial"
    
    def test_typo_in_title(self):
        existing = ["machine-learning", "deep-learning"]
        result = generate_slug_with_fallback("machne-learning", existing, similarity_threshold=0.7)
        assert result['matched_slug'] == "machine-learning"
    
    def test_abbreviated_title(self):
        existing = ["frontend-development", "backend-development"]
        result = generate_slug_with_fallback("frontend", existing, similarity_threshold=0.5)
        assert result['matched_slug'] == "frontend-development"
    
    def test_case_insensitive_match(self):
        existing = ["Hello-World", "Test-Slug"]
        result = generate_slug_with_fallback("hello world", existing)
        assert result['source'] == "exact_match"


class TestEdgeCases:
    def test_very_long_input(self):
        long_input = "a" * 1000
        existing = ["a" * 100]
        result = generate_slug_with_fallback(long_input, existing)
        assert result['slug'] is not None
    
    def test_unicode_characters(self):
        existing = ["test-slug"]
        result = generate_slug_with_fallback("你好🌟世界", existing)
        assert result['slug'] is not None
    
    def test_numbers_in_title(self):
        existing = ["python-3-tutorial"]
        result = generate_slug_with_fallback("python 3", existing, similarity_threshold=0.5)
        assert result['matched_slug'] == "python-3-tutorial"
    
    def test_hyphenated_input(self):
        existing = ["hello-world"]
        result = generate_slug_with_fallback("hello-world", existing)
        assert result['source'] == "exact_match"
    
    def test_threshold_boundary(self):
        existing = ["completely-different-slug"]
        result_low = generate_slug_with_fallback("hello", existing, similarity_threshold=0.3)
        result_high = generate_slug_with_fallback("hello", existing, similarity_threshold=0.99)
        assert result_low['source'] == 'generated'
        assert result_high['source'] == 'generated'
