// Utility functions
function calculateReturns(prices) {
    return prices.slice(1).map((price, index) => 
        (price - prices[index]) / prices[index]
    );
}

// Data fetching functions
async function fetchDataAndPlot() {
    const symbol = document.getElementById('symbol').value.toUpperCase();
    const period = document.getElementById('period').value;
    
    console.log(`Fetching data for ${symbol} over ${period}`);
    
    try {
        const data = await fetchStockData(symbol, period);
        console.log('Received data:', data);
        
        plotPriceHistory(data);
        plotReturnsDistribution(data);
    } catch (error) {
        console.error('Error:', error);
        alert(`Error fetching data for ${symbol}: ${error.message}`);
    }
}

async function fetchStockData(symbol, period) {
    try {
        const response = await fetch(`/fetch-data/${symbol}?period=1y`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching data for ${symbol}:`, error);
        alert(`Failed to fetch data for ${symbol}: ${error.message}`);
        throw error;
    }
}

async function runSimulation() {
    const symbol = document.getElementById('symbol').value;
    const nSimulations = document.getElementById('n_simulations').value;
    const nSteps = document.getElementById('n_steps').value;
    const nStates = document.getElementById('n_states').value;
    const discretizationMethod = document.getElementById('discretization_method').value;

    try {
        const response = await fetch(`/simulate/${symbol}?n_simulations=${nSimulations}&n_steps=${nSteps}&n_states=${nStates}&discretization_method=${discretizationMethod}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Received simulation data:", data);

        if (!data || !data.simulated_prices || !Array.isArray(data.simulated_prices)) {
            throw new Error('Invalid data structure received from server');
        }

        plotSimulatedPrices(data.simulated_prices);
        plotTransitionMatrix(data.transition_matrix);
        
        return data; // Return the data for potential further use
    } catch (error) {
        console.error('Error:', error);
        alert(`Error running simulation for ${symbol}: ${error.message}`);
        throw error; // Re-throw the error for the caller to handle if needed
    }
}

// Plotting functions for individual stocks
function plotPriceHistory(data) {
    const dates = Object.keys(data.data);
    const prices = Object.values(data.data);

    const trace = {
        x: dates,
        y: prices,
        type: 'scatter',
        mode: 'lines',
        name: data.symbol
    };

    const layout = {
        title: `Price History - ${data.symbol}`,
        xaxis: { title: 'Date' },
        yaxis: { title: 'Price ($)' }
    };

    Plotly.newPlot('price_history', [trace], layout);
}

function plotReturnsDistribution(data) {
    const prices = Object.values(data.data);
    const returns = prices.slice(1).map((price, index) => (price - prices[index]) / prices[index]);

    const trace = {
        x: returns,
        type: 'histogram',
        name: 'Returns'
    };

    const layout = {
        title: `Returns Distribution - ${data.symbol}`,
        xaxis: { title: 'Return (%)' },
        yaxis: { title: 'Frequency' }
    };

    Plotly.newPlot('returns_distribution', [trace], layout);
}

function plotSimulatedPrices(simulatedPrices) {
    const traces = simulatedPrices.slice(0, 10).map((prices, index) => ({
        y: prices,
        type: 'scatter',
        mode: 'lines',
        name: `Simulation ${index + 1}`
    }));

    const layout = {
        title: 'Simulated Stock Prices',
        xaxis: { title: 'Time Steps' },
        yaxis: { title: 'Price' }
    };

    Plotly.newPlot('simulated_prices', traces, layout);
}

// Comparison-related functions
let comparisonStocks = [];

function addComparisonStock() {
    const symbol = document.getElementById('compare_symbol').value.toUpperCase();
    if (!comparisonStocks.includes(symbol)) {
        comparisonStocks.push(symbol);
        updateComparisonStocksList();
        updateComparisonCharts();
    }
}

function removeComparisonStock(symbol) {
    comparisonStocks = comparisonStocks.filter(s => s !== symbol);
    updateComparisonStocksList();
    updateComparisonCharts();
}

function updateComparisonStocksList() {
    const container = document.getElementById('comparison_stocks');
    container.innerHTML = comparisonStocks.map(symbol => 
        `<span class="comparison-stock">${symbol} <span class="remove-stock" onclick="removeComparisonStock('${symbol}')">&times;</span></span>`
    ).join('');
}

async function updateComparisonCharts() {
    const comparisonStocksElement = document.getElementById('comparison_stocks');
    if (!comparisonStocksElement) {
        console.error("Element with id 'comparison_stocks' not found");
        return;
    }
    
    const comparisonStocks = comparisonStocksElement.textContent.split(',').map(s => s.trim()).filter(s => s);
    console.log("Updating comparison charts for stocks:", comparisonStocks);

    if (comparisonStocks.length === 0) {
        console.log("No stocks to compare");
        return;
    }

    const comparisonData = {};

    for (const symbol of comparisonStocks) {
        try {
            console.log(`Fetching data for ${symbol}`);
            const stockData = await fetchStockData(symbol);
            console.log(`Running simulation for ${symbol}`);
            const simulationData = await runSimulation(symbol);
            comparisonData[symbol] = {
                stockData: stockData,
                simulationData: simulationData
            };
            console.log(`Data processed for ${symbol}:`, comparisonData[symbol]);
        } catch (error) {
            console.error(`Error processing ${symbol}:`, error);
            alert(`Failed to process data for ${symbol}: ${error.message}`);
            // Remove the failed stock from the comparison list
            comparisonStocksElement.textContent = comparisonStocksElement.textContent
                .split(',')
                .filter(s => s.trim() !== symbol)
                .join(', ');
        }
    }

    console.log("Comparison data:", comparisonData);

    if (Object.keys(comparisonData).length > 0) {
        console.log("Plotting comparison charts");
        try {
            plotComparisonPriceHistory(comparisonData);
            plotComparisonReturnsDistribution(comparisonData);
            plotComparisonSimulations(comparisonData);
        } catch (error) {
            console.error("Error plotting comparison charts:", error);
            alert("Error plotting comparison charts. See console for details.");
        }
    } else {
        console.error("No valid data for comparison charts");
        alert("Unable to generate comparison charts. Please check the entered stock symbols.");
    }
}

function plotComparisonPriceHistory(comparisonData) {
    console.log("Plotting comparison price history:", comparisonData);
    const traces = [];
    
    for (const [symbol, data] of Object.entries(comparisonData)) {
        if (data.stockData && data.stockData.data) {
            const prices = Object.values(data.stockData.data);
            const dates = Object.keys(data.stockData.data);
            
            traces.push({
                x: dates,
                y: prices,
                type: 'scatter',
                mode: 'lines',
                name: symbol
            });
        } else {
            console.warn(`No valid stock data for ${symbol}`);
        }
    }

    const layout = {
        title: 'Comparison of Historical Stock Prices',
        xaxis: { title: 'Date' },
        yaxis: { title: 'Price' }
    };

    Plotly.newPlot('comparison_price_history', traces, layout);
}

function plotComparisonReturnsDistribution(comparisonData) {
    console.log("Plotting comparison returns distribution:", comparisonData);
    const traces = [];
    
    for (const [symbol, data] of Object.entries(comparisonData)) {
        if (data.stockData && data.stockData.data) {
            const prices = Object.values(data.stockData.data);
            const returns = prices.slice(1).map((price, i) => (price - prices[i]) / prices[i]);
            
            traces.push({
                x: returns,
                type: 'histogram',
                name: symbol,
                opacity: 0.7,
                nbinsx: 30
            });
        } else {
            console.warn(`No valid stock data for ${symbol}`);
        }
    }

    const layout = {
        title: 'Comparison of Returns Distribution',
        xaxis: { title: 'Returns' },
        yaxis: { title: 'Frequency' },
        barmode: 'overlay'
    };

    Plotly.newPlot('comparison_returns_distribution', traces, layout);
}

function plotComparisonSimulations(comparisonData) {
    console.log("Plotting comparison simulations:", comparisonData);
    const traces = [];
    
    for (const [symbol, data] of Object.entries(comparisonData)) {
        if (data.simulationData && data.simulationData.simulated_prices && data.simulationData.simulated_prices.length > 0) {
            const simulatedPrices = data.simulationData.simulated_prices[0]; // Use the first simulation for comparison
            
            traces.push({
                y: simulatedPrices,
                type: 'scatter',
                mode: 'lines',
                name: symbol
            });
        } else {
            console.warn(`No valid simulation data for ${symbol}`);
        }
    }

    const layout = {
        title: 'Comparison of Simulated Stock Prices',
        xaxis: { title: 'Time Steps' },
        yaxis: { title: 'Price' }
    };

    Plotly.newPlot('comparison_simulations', traces, layout);
}

// Event listeners and initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed');
    
    const fetchDataBtn = document.getElementById('fetch-data-btn');
    if (fetchDataBtn) {
        console.log('Fetch Data button found');
        fetchDataBtn.addEventListener('click', function(event) {
            event.preventDefault();
            console.log('Fetch Data button clicked');
            fetchDataAndPlot();
        });
    } else {
        console.error('Fetch Data button not found');
    }

    const addComparisonBtn = document.getElementById('add_comparison');
    if (addComparisonBtn) {
        addComparisonBtn.addEventListener('click', function() {
            const symbol = document.getElementById('compare_symbol').value.trim().toUpperCase();
            if (symbol) {
                const comparisonStocks = document.getElementById('comparison_stocks');
                if (comparisonStocks.textContent.includes(symbol)) {
                    alert(`${symbol} is already in the comparison list.`);
                } else {
                    comparisonStocks.textContent += (comparisonStocks.textContent ? ', ' : '') + symbol;
                    document.getElementById('compare_symbol').value = '';
                    updateComparisonCharts();
                }
            } else {
                alert('Please enter a valid stock symbol.');
            }
        });
    }

    const runSimulationBtn = document.getElementById('run_simulation');
    if (runSimulationBtn) {
        runSimulationBtn.addEventListener('click', runSimulation);
    } else {
        console.error('Run Simulation button not found');
    }

    // ... other code ...
});

function plotTransitionMatrix(transitionMatrix) {
    const data = [{
        z: transitionMatrix,
        type: 'heatmap',
        colorscale: 'Viridis'
    }];

    const layout = {
        title: 'Transition Probability Matrix',
        xaxis: { title: 'To State' },
        yaxis: { title: 'From State' }
    };

    Plotly.newPlot('transition_matrix', data, layout);
}
