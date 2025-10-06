"""
Page pool manager for parallel processing with shared session.

Manages multiple pages (tabs) within a single browser context.
All pages share the same authenticated session.
"""

import asyncio
from typing import List
from playwright.async_api import BrowserContext, Page
from jdp_scraper import config


class PagePool:
    """
    Manages multiple pages (tabs) in a single browser context.
    
    All pages share the same session (cookies, authentication).
    This allows parallel processing without multiple login attempts.
    
    Features:
    - Single session shared across all pages
    - Parallel navigation
    - Thread-safe page access
    - Automatic cleanup
    
    Example:
        context = await browser.new_context()
        
        # Login on first page
        page_0 = await context.new_page()
        await login_async(page_0)
        
        # Create pool with logged-in page
        pool = PagePool(context, num_pages=5)
        await pool.initialize(first_page=page_0)
        await pool.navigate_all_to_inventory()
        
        # All pages now on inventory, sharing the session!
        page = pool.get_page(0)
        
        await pool.close_all()
    """
    
    def __init__(self, context: BrowserContext, num_pages: int = 5):
        """
        Initialize the page pool.
        
        Args:
            context: Browser context (session container)
            num_pages: Total number of pages to create
        """
        self.context = context
        self.num_pages = num_pages
        self.pages: List[Page] = []
        self._initialized = False
        self._lock = asyncio.Lock()
        
    async def initialize(self, first_page: Page = None):
        """
        Initialize the page pool by creating pages.
        
        Args:
            first_page: Already logged-in page (optional, will be included in pool)
        """
        if self._initialized:
            print("[PAGE_POOL] Already initialized")
            return
        
        print(f"[PAGE_POOL] Initializing {self.num_pages} pages...")
        
        # Add first page if provided
        if first_page:
            self.pages.append(first_page)
            print(f"[PAGE_POOL] Added existing page 1/{self.num_pages}")
            start_index = 1
        else:
            start_index = 0
        
        # Create additional pages
        for i in range(start_index, self.num_pages):
            page = await self.context.new_page()
            self.pages.append(page)
            print(f"[PAGE_POOL] Created page {i + 1}/{self.num_pages}")
        
        self._initialized = True
        print(f"[PAGE_POOL] Initialization complete ({len(self.pages)} pages)")
        
    async def navigate_all_to_inventory(self):
        """
        Navigate all pages to inventory URL.
        
        Pages inherit the session from context, so they're already logged in!
        """
        if not self._initialized:
            raise RuntimeError("Page pool not initialized. Call initialize() first.")
        
        print(f"[PAGE_POOL] Navigating all pages to inventory...")
        
        # Navigate all pages except the first (already on inventory)
        tasks = []
        for i, page in enumerate(self.pages):
            if i == 0:
                continue  # First page already on inventory
            
            task = page.goto(config.INVENTORY_URL, wait_until="networkidle", timeout=20000)
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks)
        
        print(f"[PAGE_POOL] All {len(self.pages)} pages on inventory")
        
    def get_page(self, index: int) -> Page:
        """
        Get page by index.
        
        Args:
            index: Page index (0 to num_pages-1)
            
        Returns:
            The requested page
            
        Raises:
            IndexError: If index is out of range
            RuntimeError: If pool is not initialized
        """
        if not self._initialized:
            raise RuntimeError("Page pool not initialized. Call initialize() first.")
            
        if index < 0 or index >= len(self.pages):
            raise IndexError(f"Page index {index} out of range (0-{len(self.pages)-1})")
            
        return self.pages[index]
        
    async def close_all(self):
        """
        Close all pages in the pool.
        
        This should be called during cleanup.
        """
        if not self._initialized:
            return
            
        print(f"[PAGE_POOL] Closing {len(self.pages)} pages...")
        
        for i, page in enumerate(self.pages):
            try:
                if not page.is_closed():
                    await page.close()
                    print(f"[PAGE_POOL] Closed page {i + 1}/{len(self.pages)}")
            except Exception as e:
                print(f"[PAGE_POOL] Error closing page {i}: {e}")
                
        self.pages.clear()
        self._initialized = False
        print("[PAGE_POOL] All pages closed")
        
    async def get_statistics(self) -> dict:
        """
        Get statistics about the page pool.
        
        Returns:
            Dictionary with pool statistics
        """
        stats = {
            'num_pages': self.num_pages,
            'initialized': self._initialized,
            'pages_created': len(self.pages),
        }
        
        if self._initialized:
            # Count open vs closed pages
            open_pages = sum(1 for p in self.pages if not p.is_closed())
            stats['open_pages'] = open_pages
            stats['closed_pages'] = len(self.pages) - open_pages
            
        return stats
        
    async def print_statistics(self) -> None:
        """Print formatted statistics to console (ASCII only)."""
        stats = await self.get_statistics()
        
        print("\n" + "="*60)
        print("PAGE POOL STATISTICS")
        print("="*60)
        print(f"Number of pages    : {stats['num_pages']}")
        print(f"Initialized        : {stats['initialized']}")
        print(f"Pages created      : {stats['pages_created']}")
        
        if stats['initialized']:
            print(f"Open pages         : {stats['open_pages']}")
            print(f"Closed pages       : {stats['closed_pages']}")
            
        print("="*60 + "\n")
        
    def __len__(self) -> int:
        """Return the number of pages in the pool."""
        return len(self.pages)
