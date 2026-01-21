"""
Analyze image content patterns from YOLO detections
Task 3 - Business Questions Analysis
"""
import sys
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

print("=" * 70)
print("TASK 3: IMAGE CONTENT ANALYSIS")
print("=" * 70)
print()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medical_warehouse")
engine = create_engine(DATABASE_URL)

# ============================================================================
# Question 1: Do "promotional" posts (with people) get more views than 
#             "product_display" posts?
# ============================================================================
print("=" * 70)
print("Q1: Do 'promotional' posts (with people) get more views than")
print("    'product_display' posts?")
print("=" * 70)
print()

try:
    q1_query = """
        SELECT 
            image_category,
            COUNT(*) as message_count,
            ROUND(AVG(view_count)::NUMERIC, 2) as avg_views,
            ROUND(AVG(forward_count)::NUMERIC, 2) as avg_forwards,
            ROUND(MIN(view_count)::NUMERIC, 2) as min_views,
            ROUND(MAX(view_count)::NUMERIC, 2) as max_views,
            ROUND(SUM(view_count)::NUMERIC, 0) as total_views
        FROM fct_image_detections
        WHERE image_category IN ('promotional', 'product_display')
        GROUP BY image_category
        ORDER BY avg_views DESC
    """
    
    q1_results = pd.read_sql(q1_query, engine)
    print(q1_results.to_string(index=False))
    print()
    
    # Compare promotional vs product_display
    promotional = q1_results[q1_results['image_category'] == 'promotional']
    product_display = q1_results[q1_results['image_category'] == 'product_display']
    
    if not promotional.empty and not product_display.empty:
        promo_avg = promotional['avg_views'].iloc[0]
        prod_avg = product_display['avg_views'].iloc[0]
        
        if promo_avg > prod_avg:
            diff = ((promo_avg - prod_avg) / prod_avg) * 100
            print(f"✓ Promotional posts get {diff:.1f}% MORE views on average")
            print(f"  Promotional: {promo_avg:.2f} avg views")
            print(f"  Product Display: {prod_avg:.2f} avg views")
        else:
            diff = ((prod_avg - promo_avg) / promo_avg) * 100
            print(f"✗ Product display posts get {diff:.1f}% MORE views on average")
            print(f"  Product Display: {prod_avg:.2f} avg views")
            print(f"  Promotional: {promo_avg:.2f} avg views")
    print()
    
except Exception as e:
    print(f"Error: {e}")
    print()

# ============================================================================
# Question 2: Which channels use more visual content?
# ============================================================================
print("=" * 70)
print("Q2: Which channels use more visual content?")
print("=" * 70)
print()

try:
    q2_query = """
        SELECT 
            dc.channel_name,
            dc.channel_type,
            COUNT(DISTINCT fm.message_id) as total_messages,
            COUNT(DISTINCT fid.message_id) as messages_with_detections,
            ROUND(
                COUNT(DISTINCT fid.message_id)::NUMERIC / 
                NULLIF(COUNT(DISTINCT fm.message_id), 0) * 100, 
                2
            ) as detection_coverage_pct,
            ROUND(AVG(fid.detection_count)::NUMERIC, 2) as avg_objects_per_image
        FROM dim_channels dc
        LEFT JOIN fct_messages fm ON dc.channel_key = fm.channel_key
        LEFT JOIN fct_image_detections fid ON fm.message_id = fid.message_id
        GROUP BY dc.channel_name, dc.channel_type
        ORDER BY detection_coverage_pct DESC, avg_objects_per_image DESC
    """
    
    q2_results = pd.read_sql(q2_query, engine)
    print(q2_results.to_string(index=False))
    print()
    
    # Show top channel
    if not q2_results.empty:
        top_channel = q2_results.iloc[0]
        print(f"Top channel for visual content: {top_channel['channel_name']}")
        print(f"  - {top_channel['detection_coverage_pct']:.1f}% of messages have detections")
        print(f"  - Average {top_channel['avg_objects_per_image']:.1f} objects per image")
    print()
    
except Exception as e:
    print(f"Error: {e}")
    print()

# ============================================================================
# Question 3: What are the limitations of using pre-trained models for 
#             domain-specific tasks?
# ============================================================================
print("=" * 70)
print("Q3: Limitations Analysis - Pre-trained Models for Domain-Specific Tasks")
print("=" * 70)
print()

try:
    # Show detected object distribution
    q3a_query = """
        SELECT 
            detected_objects,
            COUNT(*) as count
        FROM fct_image_detections
        WHERE detected_objects IS NOT NULL
            AND detected_objects != ''
        GROUP BY detected_objects
        ORDER BY count DESC
        LIMIT 20
    """
    
    q3a_results = pd.read_sql(q3a_query, engine)
    print("Top 20 Detected Object Combinations:")
    print("-" * 70)
    print(q3a_results.to_string(index=False))
    print()
    
    # Show category distribution
    q3b_query = """
        SELECT 
            image_category,
            COUNT(*) as count,
            ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 2) as percentage
        FROM fct_image_detections
        GROUP BY image_category
        ORDER BY count DESC
    """
    
    q3b_results = pd.read_sql(q3b_query, engine)
    print("Image Category Distribution:")
    print("-" * 70)
    print(q3b_results.to_string(index=False))
    print()
    
    # Show confidence scores
    q3c_query = """
        SELECT 
            image_category,
            ROUND(AVG(confidence_score)::NUMERIC, 3) as avg_confidence,
            ROUND(MIN(confidence_score)::NUMERIC, 3) as min_confidence,
            ROUND(MAX(confidence_score)::NUMERIC, 3) as max_confidence,
            COUNT(CASE WHEN confidence_score < 0.3 THEN 1 END) as low_confidence_count
        FROM fct_image_detections
        WHERE confidence_score IS NOT NULL
        GROUP BY image_category
        ORDER BY avg_confidence DESC
    """
    
    q3c_results = pd.read_sql(q3c_query, engine)
    print("Confidence Score Analysis by Category:")
    print("-" * 70)
    print(q3c_results.to_string(index=False))
    print()
    
    print("LIMITATIONS IDENTIFIED:")
    print("-" * 70)
    print("1. General Object Detection: YOLO detects general objects (person, bottle)")
    print("   but cannot identify specific medical products or brands")
    print("2. Limited Product Classes: COCO dataset has limited medical/pharmaceutical")
    print("   product classes, so many products may be misclassified or missed")
    print("3. Context Understanding: Cannot understand product context, usage,")
    print("   or medical information in images")
    print("4. Text in Images: Cannot read text overlays, labels, or product names")
    print("5. Domain-Specific Features: Cannot detect medical-specific features like")
    print("   dosage information, expiration dates, or regulatory labels")
    print()
    
except Exception as e:
    print(f"Error: {e}")
    print()

# ============================================================================
# Additional Analysis: Image Content Patterns
# ============================================================================
print("=" * 70)
print("ADDITIONAL ANALYSIS: Image Content Patterns")
print("=" * 70)
print()

try:
    # Engagement by image category
    additional_query = """
        SELECT 
            image_category,
            COUNT(*) as message_count,
            ROUND(AVG(view_count)::NUMERIC, 2) as avg_views,
            ROUND(AVG(forward_count)::NUMERIC, 2) as avg_forwards,
            ROUND(AVG(detection_count)::NUMERIC, 2) as avg_objects,
            ROUND(AVG(confidence_score)::NUMERIC, 3) as avg_confidence
        FROM fct_image_detections
        GROUP BY image_category
        ORDER BY avg_views DESC
    """
    
    additional_results = pd.read_sql(additional_query, engine)
    print("Engagement Metrics by Image Category:")
    print("-" * 70)
    print(additional_results.to_string(index=False))
    print()
    
except Exception as e:
    print(f"Error: {e}")
    print()

print("=" * 70)
print("[SUCCESS] ANALYSIS COMPLETE")
print("=" * 70)
