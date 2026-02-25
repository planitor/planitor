#!/usr/bin/env python3
"""
Clean up duplicate minutes in the database.
For each meeting + case combination with multiple minutes, keep only the one
with the shortest headline (assuming the longer one has inquiry text concatenated).
"""
import sys
sys.path.insert(0, '/code')

from planitor.database import SessionLocal
from planitor.models import Meeting, Minute, Council
from sqlalchemy import func
from collections import defaultdict

def main(dry_run=True):
    db = SessionLocal()
    
    # Find all minutes grouped by meeting_id + case_id
    all_minutes = db.query(Minute).all()
    
    # Group by (meeting_id, case_id)
    groups = defaultdict(list)
    for m in all_minutes:
        key = (m.meeting_id, m.case_id)
        groups[key].append(m)
    
    # Find duplicates and decide which to keep
    to_delete = []
    for (meeting_id, case_id), minutes in groups.items():
        if len(minutes) > 1:
            # Sort by headline length - keep shortest (cleanest)
            sorted_mins = sorted(minutes, key=lambda x: len(x.headline or ''))
            keep = sorted_mins[0]
            delete = sorted_mins[1:]
            to_delete.extend(delete)
            
            if len(to_delete) <= 10:  # Show first few examples
                meeting = db.query(Meeting).get(meeting_id)
                print(f"\nMeeting {meeting.name if meeting else meeting_id}, Case {case_id}:")
                print(f"  KEEP: serial={keep.serial}, headline={keep.headline[:50] if keep.headline else 'None'}...")
                for d in delete:
                    print(f"  DELETE: serial={d.serial}, headline={d.headline[:50] if d.headline else 'None'}...")
    
    print(f"\n\nTotal minutes to delete: {len(to_delete)}")
    
    if dry_run:
        print("\nDRY RUN - no changes made. Run with --execute to delete.")
    else:
        print("\nDeleting duplicates...")
        for minute in to_delete:
            db.delete(minute)
        db.commit()
        print("Done!")
    
    db.close()

if __name__ == "__main__":
    dry_run = "--execute" not in sys.argv
    main(dry_run=dry_run)
