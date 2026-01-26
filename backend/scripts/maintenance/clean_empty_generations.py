#!/usr/bin/env python3
"""
Script para limpar pedidos em status GENERATING que não têm arquivos gerados.
Permite resetar esses pedidos para status BUILDING para que possam ser regenerados.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.models.site_order import SiteOrder, SiteOrderStatus
from sqlalchemy import select
from app.services.site_generator_service import SiteGeneratorService
import shutil

async def clean_empty_generations(dry_run: bool = True):
    """Find and clean orders in GENERATING status with no files"""
    async with AsyncSessionLocal() as db:
        # Get all orders in GENERATING status
        result = await db.execute(
            select(SiteOrder).where(SiteOrder.status == SiteOrderStatus.GENERATING)
        )
        generating_orders = result.scalars().all()
        
        service = SiteGeneratorService(db)
        empty_orders = []
        
        print(f"Found {len(generating_orders)} orders in GENERATING status\n")
        
        for order in generating_orders:
            target_dir = service._get_target_dir(order.id)
            stage_info = service._check_stage_files(target_dir)
            
            # Consider empty if no files or very few files (< 5)
            if stage_info["files_count"] < 5:
                empty_orders.append({
                    "order": order,
                    "target_dir": target_dir,
                    "files_count": stage_info["files_count"],
                    "stage_info": stage_info
                })
                print(f"Order {order.id} ({order.customer_name}): {stage_info['files_count']} files - EMPTY")
            else:
                print(f"Order {order.id} ({order.customer_name}): {stage_info['files_count']} files - OK")
        
        print(f"\n{'='*60}")
        print(f"Total empty generations: {len(empty_orders)}")
        
        if not empty_orders:
            print("No empty generations found!")
            return
        
        if dry_run:
            print("\n[DRY RUN] Would reset the following orders:")
            for item in empty_orders:
                order = item["order"]
                print(f"  - Order {order.id}: {order.customer_name} ({order.customer_email})")
                print(f"    Files: {item['files_count']}, Directory: {item['target_dir']}")
            print("\nRun with --execute to actually reset these orders")
        else:
            print("\n[EXECUTING] Resetting empty generations...")
            reset_count = 0
            
            for item in empty_orders:
                order = item["order"]
                target_dir = item["target_dir"]
                
                try:
                    # Remove directory if it exists
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir)
                        print(f"  ✓ Removed directory for order {order.id}")
                    
                    # Reset status to BUILDING
                    order.status = SiteOrderStatus.BUILDING
                    order.admin_notes = f"Auto-reset: Generation had {item['files_count']} files (too few). Ready for retry."
                    await db.commit()
                    
                    reset_count += 1
                    print(f"  ✓ Reset order {order.id} to BUILDING status")
                except Exception as e:
                    print(f"  ✗ Error resetting order {order.id}: {e}")
            
            print(f"\n✅ Successfully reset {reset_count} orders")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean empty site generations")
    parser.add_argument("--execute", action="store_true", help="Actually execute the cleanup (default is dry-run)")
    args = parser.parse_args()
    
    asyncio.run(clean_empty_generations(dry_run=not args.execute))
