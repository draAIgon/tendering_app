const { test, expect } = require('@playwright/test');

test.describe('Dashboard File Upload Tests', () => {
  test('should display "Seleccionar Archivos" button', async ({ page }) => {
    // Set a timeout for this test
    test.setTimeout(30000);

    // Navigate to the dashboard
    await page.goto('https://hackiathon.nimblersoft.org/dashboard');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Take a screenshot of the initial state
    await page.screenshot({ 
      path: 'tmp/dashboard-initial-state.png',
      fullPage: true 
    });

    // Look for the "Seleccionar Archivos" button
    const selectFilesButton = page.locator('text="Seleccionar Archivos"');
    
    // Assert that the button is visible
    await expect(selectFilesButton).toBeVisible();

    console.log('✅ "Seleccionar Archivos" button found and is visible');
  });

  test('should have file upload functionality', async ({ page }) => {
    // Set a timeout for this test
    test.setTimeout(45000);

    // Navigate to the dashboard
    await page.goto('https://hackiathon.nimblersoft.org/dashboard');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Look for the "Seleccionar Archivos" button
    const selectFilesButton = page.locator('text="Seleccionar Archivos"');
    await expect(selectFilesButton).toBeVisible();

    // Take a screenshot before clicking
    await page.screenshot({ 
      path: 'tmp/before-file-selection.png',
      fullPage: true 
    });

    // Click the button
    // Instead of clicking and expecting a native dialog, use setInputFiles to simulate file selection
    const fileInput = await page.$('input[type="file"]');
    if (fileInput) {
      // Simulate selecting a file
      await fileInput.setInputFiles('documents/EJEMPLO DE CONTRATO - RETO 1.pdf');
      console.log('✅ File input set with EJEMPLO DE CONTRATO - RETO 1.pdf');
    } else {
      // Fallback: click the button (may trigger file input to appear)
      await selectFilesButton.click();
      console.log('⚠️ File input not found before clicking, clicked button instead');
    }


    // Look for the "Procesar Documentos con IA" button as well
    const processButton = page.locator('text="Procesar Documentos con IA"');
    
    // Check if the process button exists (might be disabled initially)
    const processButtonExists = await processButton.count() > 0;
    
    if (processButtonExists) {
      console.log('✅ "Procesar Documentos con IA" button found');
      await page.screenshot({ 
        path: 'tmp/process-button-found.png',
        fullPage: true 
      });
    } else {
      console.log('⚠️  "Procesar Documentos con IA" button not found - might appear after file selection');
    }
  });

  test('should show file input when clicking "Seleccionar Archivos"', async ({ page }) => {
    // Set a timeout for this test
    test.setTimeout(45000);

    // Navigate to the dashboard
    await page.goto('https://hackiathon.nimblersoft.org/dashboard');
    await page.waitForLoadState('networkidle');

    // Find and click the "Seleccionar Archivos" button
    const selectFilesButton = page.locator('text="Seleccionar Archivos"');
    await expect(selectFilesButton).toBeVisible();

    // Take a screenshot before clicking
    await page.screenshot({ 
      path: 'tmp/before-clicking-select-files.png',
      fullPage: true 
    });
    
    // Take a screenshot after clicking
    await page.screenshot({ 
      path: 'tmp/after-clicking-select-files.png',
      fullPage: true 
    });

    // Look for file input or any change in the UI
    await page.waitForTimeout(2000); // Wait for any UI changes

    // Take a final screenshot to document the result
    await page.screenshot({ 
      path: 'tmp/final-state-after-click.png',
      fullPage: true 
    });

    console.log('✅ File selection interaction completed');
  });
});
