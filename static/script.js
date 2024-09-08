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
    const response = await fetch(`/fetch-data/${symbol}?period=${period}`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

async function runSimulation() {
    const symbol = document.getElementById('symbol').value;
    const n_simulations = document.getElementById('n_simulations').value;
    const n_steps = document.getElementById('n_steps').value;
    const n_states = document.getElementById('n_states').value;
    const discretization_method = document.getElementById('discretization_method').value;

    try {
        const response = await fetch(`/simulate/${symbol}?n_simulations=${n_simulations}&n_steps=${n_steps}&n_states=${n_states}&discretization_method=${discretization_method}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Simulation data:', data);  // Add this line for debugging
        
        if (data.simulated_prices) {
            plotSimulatedPrices(data.simulated_prices);
        } else {
            console.error('Simulated prices not found in the response');
        }
        
        if (data.transition_matrix) {
            plotTransitionMatrix(data.transition_matrix);
        } else {
            console.error('Transition matrix not found in the response');
        }
    } catch (error) {
        console.error('Error running simulation:', error);
        alert(`Error running simulation for ${symbol}: ${error.message}`);
    }
}

// Plotting functions for individual stocks
function plotPriceHistory(data) {
    console.log('Plotting price history', data);
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
        title: {
            text: `Price History - ${data.symbol}`,
            font: { size: 24 }
        },
        xaxis: { 
            title: 'Date',
            tickangle: -45
        },
        yaxis: { 
            title: 'Price ($)',
            tickformat: '$.2f'
        },
        showlegend: true,
        legend: {
            x: 1,
            xanchor: 'right',
            y: 1
        }
    };

    Plotly.newPlot('price_history', [trace], layout);
}

function plotReturnsDistribution(data) {
    console.log('Plotting returns distribution', data);
    const prices = Object.values(data.data);
    const returns = calculateReturns(prices);

    const trace = {
        x: returns,
        type: 'histogram',
        name: 'Returns'
    };

    const layout = {
        title: {
            text: `Returns Distribution - ${data.symbol}`,
            font: { size: 24 }
        },
        xaxis: { title: 'Return (%)' },
        yaxis: { title: 'Frequency' },
        bargap: 0.05,
        showlegend: false
    };

    Plotly.newPlot('returns_distribution', [trace], layout);
}

function plotSimulatedPrices(simulatedPrices) {
    const data = simulatedPrices.map((prices, index) => ({
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

    Plotly.newPlot('simulated_prices', data, layout);
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
    const period = document.getElementById('period').value;
    const stocksData = await Promise.all(comparisonStocks.map(symbol => fetchStockData(symbol, period)));
    
    plotComparisonPriceHistory(stocksData);
    plotComparisonReturnsDistribution(stocksData);
    
    const n_simulations = document.getElementById('n_simulations').value;
    const n_steps = document.getElementById('n_steps').value;
    const n_states = document.getElementById('n_states').value;
    const discretization_method = document.getElementById('discretization_method').value;
    
    const simulationResults = await Promise.all(stocksData.map(data => 
        runSimulation(data.symbol, n_simulations, n_steps, n_states, discretization_method)
    ));
    
    plotComparisonSimulatedPrices(simulationResults);
}

function plotComparisonPriceHistory(stocksData) {
    const traces = stocksData.map(stock => ({
        x: Object.keys(stock.data),
        y: Object.values(stock.data),
        type: 'scatter',
        mode: 'lines',
        name: stock.symbol
    }));

    const layout = {
        title: 'Price History Comparison',
        xaxis: { title: 'Date' },
        yaxis: { title: 'Price ($)' },
        showlegend: true,
        legend: { orientation: 'h', y: -0.2 }
    };

    Plotly.newPlot('comparison_price_history', traces, layout);
}

function plotComparisonReturnsDistribution(stocksData) {
    const traces = stocksData.map(stock => {
        const prices = Object.values(stock.data);
        const returns = calculateReturns(prices);
        return {
            x: returns,
            type: 'histogram',
            name: stock.symbol,
            opacity: 0.6
        };
    });

    const layout = {
        title: 'Returns Distribution Comparison',
        xaxis: { title: 'Return' },
        yaxis: { title: 'Frequency' },
        barmode: 'overlay',
        showlegend: true,
        legend: { orientation: 'h', y: -0.2 }
    };

    Plotly.newPlot('comparison_returns_distribution', traces, layout);
}

function plotComparisonSimulatedPrices(simulationResults) {
    const colors = ['blue', 'red', 'green', 'purple', 'orange'];
    const lineStyles = ['solid', 'dash', 'dot', 'dashdot'];
    const traces = [];

    simulationResults.forEach((result, stockIndex) => {
        // Only plot one simulation for each stock to avoid clutter
        traces.push({
            y: result.simulated_prices[0],
            type: 'scatter',
            mode: 'lines',
            name: result.symbol,
            line: {
                color: colors[stockIndex % colors.length],
                dash: lineStyles[stockIndex % lineStyles.length]
            }
        });
    });

    const layout = {
        title: 'Comparison of Simulated Stock Prices',
        xaxis: { title: 'Time Steps' },
        yaxis: { title: 'Price ($)' },
        showlegend: true
    };

    Plotly.newPlot('comparison_simulated_prices', traces, layout);
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
        addComparisonBtn.addEventListener('click', addComparisonStock);
    }

    const runSimulationBtn = document.getElementById('run_simulation');
    if (runSimulationBtn) {
        runSimulationBtn.addEventListener('click', async function() {
            const symbol = document.getElementById('symbol').value;
            const n_simulations = document.getElementById('n_simulations').value;
            const n_steps = document.getElementById('n_steps').value;
            const n_states = document.getElementById('n_states').value;
            const discretization_method = document.getElementById('discretization_method').value;

            try {
                const data = await runSimulation(symbol, n_simulations, n_steps, n_states, discretization_method);
                plotSimulatedPrices(data);
                plotTransitionMatrix(data.transition_matrix); // Add this line
            } catch (error) {
                console.error('Error:', error);
                alert(`Error running simulation for ${symbol}: ${error.message}`);
            }
        });
    }
});

function plotTransitionMatrix(transitionMatrix) {
    const data = [{
        z: transitionMatrix,
        type: 'heatmap',
        colorscale: 'Viridis'
    }];

    const layout = {
        title: 'Transition Probability Matrix',
        xaxis: {title: 'To State'},
        yaxis: {title: 'From State'}
    };

    Plotly.newPlot('transition_matrix', data, layout);
}
