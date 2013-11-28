// Initalize Grid
$(function(){ //DOM Ready

    $(".gridster ul").gridster({
        widget_margins: [10, 10],
        widget_base_dimensions: [140, 140]
    });

    // Piechart
    nv.addGraph(function() {
        var width = 450,
            height = 450;

        var chart = nv.models.pieChart()
            .x(function(d) { return d.category })
            .y(function(d) { return d.visits })
            .color(d3.scale.category10().range())
            .width(width)
            .height(height);

        d3.select("#categories_chart")
            .datum(visits_by_category)
            .transition().duration(1200)
            .attr('width', width)
            .attr('height', height)
            .call(chart);

        chart.dispatch.on('stateChange', function(e) { nv.log('New State:', JSON.stringify(e)); });

        return chart;
    });

    // Tag cloud
    var fill = d3.scale.category20();

    d3.layout.cloud().size([290, 500])
        .words(metadata_keywords.map(function(d) {
            return {text: d, size: 10 + Math.random() * 90};
        }))
        .padding(5)
        .rotate(function() { return ~~(Math.random() * 2) * 90; })
        .font("Impact")
        .fontSize(function(d) { return d.size; })
        .on("end", draw)
        .start();

    function draw(words) {
        d3.select("#tagword").append("svg")
            .attr("width", 290)
            .attr("height", 500)
            .append("g")
            .attr("transform", "translate(150,150)")
            .selectAll("text")
            .data(words)
            .enter().append("text")
            .style("font-size", function(d) { return d.size + "px"; })
            .style("font-family", "Impact")
            .style("fill", function(d, i) { return fill(i); })
            .attr("text-anchor", "middle")
            .attr("transform", function(d) {
                return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
            })
            .text(function(d) { return d.text; });
    }

    // Keywords bar histogram
    historicalBarChart = [
        {
            key: "Keywords",
            values: site_keywords
        }
    ];

    nv.addGraph(function() {
        var chart = nv.models.discreteBarChart()
                .x(function(d) { return d.keyword })
                .y(function(d) { return d.frequency })
                .staggerLabels(true)
                //.staggerLabels(historicalBarChart[0].values.length > 8)
                .tooltips(false)
                .showValues(true)
                .transitionDuration(250);

        d3.select('#chart1 svg')
            .datum(historicalBarChart)
            .call(chart);

        nv.utils.windowResize(chart.update);

        return chart;
    });

});