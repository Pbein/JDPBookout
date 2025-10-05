"""
Browser context pool manager for parallel processing.

Manages a pool of browser contexts for efficient parallel task execution.
"""

import asyncio
from typing import List
from playwright.async_api import Browser, BrowserContext


class ContextPool:
    """
    Manages a pool of browser contexts for parallel task execution.
    
    Features:
    - Round-robin context distribution
    - Resource blocking (images, CSS, fonts) for performance
    - Thread-safe context access
    - Automatic cleanup
    
    Example:
        pool = ContextPool(browser, num_contexts=5, block_resources=True)
        await pool.initialize()
        
        context = await pool.get_context()
        page = await context.new_page()
        # Use page...
        
        await pool.close_all()
    """
    
    def __init__(
        self,
        browser: Browser,
        num_contexts: int = 5,
        block_resources: bool = True
    ):
        """
        Initialize the context pool.
        
        Args:
            browser: Playwright browser instance
            num_contexts: Number of contexts to create in the pool
            block_resources: Whether to block images/CSS/fonts for performance
        """
        self.browser = browser
        self.num_contexts = num_contexts
        self.block_resources = block_resources
        
        self.contexts: List[BrowserContext] = []
        self._current_index = 0
        self._lock = asyncio.Lock()
        self._initialized = False
        
    async def initialize(self) -> None:
        """
        Initialize the context pool by creating all contexts.
        
        This should be called once after construction.
        """
        if self._initialized:
            print("[CONTEXT_POOL] Already initialized")
            return
            
        print(f"[CONTEXT_POOL] Initializing {self.num_contexts} contexts...")
        
        for i in range(self.num_contexts):
            context = await self.browser.new_context()
            
            # Block resources for performance if enabled
            if self.block_resources:
                await self._setup_resource_blocking(context)
                
            self.contexts.append(context)
            print(f"[CONTEXT_POOL] Created context {i + 1}/{self.num_contexts}")
            
        self._initialized = True
        print(f"[CONTEXT_POOL] Initialization complete")
        
    async def _setup_resource_blocking(self, context: BrowserContext) -> None:
        """
        Set up resource blocking for a context to improve performance.
        
        Blocks: images, stylesheets, fonts, media (30-50% speedup)
        
        Args:
            context: The browser context to configure
        """
        async def block_handler(route, request):
            """Block certain resource types."""
            resource_type = request.resource_type
            
            if resource_type in ['image', 'imageset', 'stylesheet', 'font', 'media']:
                await route.abort()
            else:
                await route.continue_()
                
        await context.route("**/*", block_handler)
        
    async def get_context(self) -> BrowserContext:
        """
        Get the next available context using round-robin distribution.
        
        Returns:
            A browser context from the pool
            
        Raises:
            RuntimeError: If the pool is not initialized
        """
        if not self._initialized:
            raise RuntimeError("Context pool not initialized. Call initialize() first.")
            
        async with self._lock:
            context = self.contexts[self._current_index]
            self._current_index = (self._current_index + 1) % self.num_contexts
            return context
            
    async def get_context_by_index(self, index: int) -> BrowserContext:
        """
        Get a specific context by index.
        
        Args:
            index: The context index (0 to num_contexts-1)
            
        Returns:
            The requested browser context
            
        Raises:
            IndexError: If index is out of range
            RuntimeError: If pool is not initialized
        """
        if not self._initialized:
            raise RuntimeError("Context pool not initialized. Call initialize() first.")
            
        if index < 0 or index >= self.num_contexts:
            raise IndexError(f"Context index {index} out of range (0-{self.num_contexts-1})")
            
        return self.contexts[index]
        
    async def close_all(self) -> None:
        """
        Close all contexts in the pool.
        
        This should be called during cleanup.
        """
        if not self._initialized:
            return
            
        print(f"[CONTEXT_POOL] Closing {len(self.contexts)} contexts...")
        
        for i, context in enumerate(self.contexts):
            try:
                await context.close()
                print(f"[CONTEXT_POOL] Closed context {i + 1}/{len(self.contexts)}")
            except Exception as e:
                print(f"[CONTEXT_POOL] Error closing context {i}: {e}")
                
        self.contexts.clear()
        self._initialized = False
        print("[CONTEXT_POOL] All contexts closed")
        
    async def get_statistics(self) -> dict:
        """
        Get statistics about the context pool.
        
        Returns:
            Dictionary with pool statistics
        """
        stats = {
            'num_contexts': self.num_contexts,
            'initialized': self._initialized,
            'block_resources': self.block_resources,
            'current_index': self._current_index,
        }
        
        if self._initialized:
            # Count pages in each context
            page_counts = []
            for context in self.contexts:
                page_counts.append(len(context.pages))
                
            stats['total_pages'] = sum(page_counts)
            stats['pages_per_context'] = page_counts
            stats['avg_pages_per_context'] = sum(page_counts) / len(page_counts) if page_counts else 0
            
        return stats
        
    async def print_statistics(self) -> None:
        """Print formatted statistics to console (ASCII only)."""
        stats = await self.get_statistics()
        
        print("\n" + "="*60)
        print("CONTEXT POOL STATISTICS")
        print("="*60)
        print(f"Number of contexts : {stats['num_contexts']}")
        print(f"Initialized        : {stats['initialized']}")
        print(f"Resource blocking  : {stats['block_resources']}")
        
        if stats['initialized']:
            print(f"Total pages        : {stats['total_pages']}")
            print(f"Avg pages/context  : {stats['avg_pages_per_context']:.1f}")
            print(f"Current index      : {stats['current_index']}")
            
        print("="*60 + "\n")
        
    def __len__(self) -> int:
        """Return the number of contexts in the pool."""
        return len(self.contexts)
