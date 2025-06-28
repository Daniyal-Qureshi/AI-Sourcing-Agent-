"""
Example usage of LinkedIn Profile Extractor
Demonstrates different ways to use the tool programmatically
"""
import asyncio
import json
from typing import List

# Import the main classes and functions
from main import LinkedInSourcer
from utils import search_linkedin_profiles, extract_multiple_profiles
from models import LinkedInProfile, SearchResult



async def example_full_workflow():
    """
    Example 3: Complete workflow - Search and then extract profiles
    This combines both search and extraction in one operation
    """
    print("\n🚀 Example 3: Full Workflow")
    print("=" * 40)
    
    # Initialize the main sourcer class
    sourcer = LinkedInSourcer()
    
    search_terms = ["product manager", "saas", "New York"]
    max_search_results = 15
    max_extractions = 5  # Only extract first 5 profiles
    
    try:
        # Run complete workflow
        search_result, extraction_result = await sourcer.search_and_extract(
            search_terms=search_terms,
            max_search_results=max_search_results,
            max_extractions=max_extractions,
            use_login=True
        )
        
        # Get session summary
        summary = sourcer.get_summary()
        
        print(f"\n📋 Session Summary:")
        print(f"   🔍 Search: {search_result.total_results} profiles found")
        print(f"   📊 Extraction: {extraction_result.successful_extractions}/{extraction_result.total_profiles} profiles extracted")
        print(f"   ⏱️  Total time: {extraction_result.total_time:.1f}s")
        
        # Save complete summary
        with open('workflow_summary_example.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n💾 Complete summary saved to: workflow_summary_example.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_custom_search_terms():
    """
    Example 4: Using different search term combinations
    Shows how to search for different types of professionals
    """
    print("\n🎯 Example 4: Custom Search Terms")
    print("=" * 40)
    
    # Different search combinations
    search_scenarios = [
        {
            "name": "Frontend Developers in Tech",
            "terms": ["frontend developer", "react", "startup"],
            "max_results": 5
        },
        {
            "name": "Data Scientists in Healthcare", 
            "terms": ["data scientist", "machine learning", "healthcare"],
            "max_results": 5
        },
        {
            "name": "DevOps Engineers in Finance",
            "terms": ["devops engineer", "kubernetes", "fintech"],
            "max_results": 5
        }
    ]
    
    for scenario in search_scenarios:
        print(f"\n🔍 Searching: {scenario['name']}")
        print(f"   Terms: {scenario['terms']}")
        
        try:
            search_result = await search_linkedin_profiles(
                scenario['terms'], 
                scenario['max_results']
            )
            
            print(f"   ✅ Found: {search_result.total_results} profiles")
            
            # Show first few results
            for i, url in enumerate(search_result.profiles[:3], 1):
                print(f"      {i}. {url}")
            
            if len(search_result.profiles) > 3:
                print(f"      ... and {len(search_result.profiles) - 3} more")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


async def main():
    """
    Main function to run all examples
    You can comment out examples you don't want to run
    """
    print("🚀 LinkedIn Profile Extractor - Usage Examples")
    print("=" * 60)
    
    await example_full_workflow()

if __name__ == "__main__":
    # Run the examples
    asyncio.run(main()) 