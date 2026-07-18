async page => {
    console.log("Navigating to Flow home...");
    await page.goto('https://labs.google/fx/tools/flow');
    await page.waitForLoadState('networkidle');
    
    console.log("Clicking New Project...");
    await page.getByRole('button', { name: 'add_2 New project' }).click();
    await page.waitForTimeout(4000);
    
    console.log("Closing Agent panel...");
    try {
        await page.getByRole('button', { name: 'close Close' }).click({timeout: 2000});
        console.log("Agent panel closed.");
    } catch(e) {
        console.log("Agent panel not found.");
    }
}
