define([
    'jquery',
    'base/js/utils'
], function ($, utils) {
    function setupDOM() {
        // checkpoint button
        $('#maintoolbar-container').append(
            $('<div>')
                .addClass('btn-group')
                .addClass('pull-right')
                .append(
                    $('<a>')
                        .addClass('btn')
                        .addClass('btn-default')
                        .css('border', 'none')
                        .css('color', '#00aa00')
                        .attr('href', '/hub/migrate?checkpoint=true')
                        .append(
                            $('<i>')
                                .addClass('fas fa-pause')
                                .addClass('checkpoint-icon')
                                .css('padding', '0px 8px')
                        )
                )
                .append(
                    $('<a>')
                        .addClass('btn')
                        .addClass('btn-default')
                        .css('border', 'none')
                        .css('color', '#00aa00')
                        .attr('id', 'checkpoint-button')
                        // .addClass('dropdown-toggle')
                        .attr('data-toggle', 'dropdown')
                        .attr('href', '#')
                        .click(function() {
                            $('#save-notebook')
                                .trigger('click');
                            return true;
                        })
                        .append(
                            $('<i>')
                                .addClass('fas fa-fast-forward')
                                .addClass('checkpoint-icon')
                                .css('padding', '0px 8px')
                        )
                )
                .append(
                    $('<ul>')
                        .addClass('dropdown-menu')
                        .attr('id', 'size-list')
                )
        );

        // nbresuse
        $('#maintoolbar-container').append(
            $('<div>')
                .attr('id', 'nbresuse-display')
                .addClass('btn-group')
                .addClass('pull-right')
                .append(
                    $('<strong>').text('Memory: ')
                ).append(
                    $('<span>')
                        .attr('id', 'nbresuse-mem')
                        .attr('title', 'Actively used Memory (updates every 5s)')
                )
        );
        // FIXME: Do something cleaner to get styles in here?
        $('head').append(
            $('<style>').html('.nbresuse-warn { background-color: #FFD2D2; color: #D8000C; }')
        );
        $('head').append(
            $('<style>').html('#nbresuse-display { padding: 2px 8px; }')
        );
        $('head').append(
            $('<style>').html('.checkpoint-icon { font-family: FontAwesome; font-style: normal; }')
        );
        $('head').append(
            $('<style>').html('#checkpoint-button { padding: 2px 0px; }')
        );
    }

    function humanFileSize(size) {
        var i = Math.floor(Math.log(size) / Math.log(1024));
        return (size / Math.pow(1024, i)).toFixed(1) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
    }

    var displayMetrics = function () {
        if (document.hidden) {
            // Don't poll when nobody is looking
            return;
        }
        $.getJSON({
            url: utils.get_body_data('baseUrl') + 'metrics',
            success: function (data) {
                totalMemoryUsage = humanFileSize(data['rss']);

                var limits = data['limits'];
                var display = totalMemoryUsage;

                if (limits['memory']) {
                    if (limits['memory']['rss']) {
                        maxMemoryUsage = humanFileSize(limits['memory']['rss']);
                        display += " / " + maxMemoryUsage
                    }
                    if (limits['memory']['warn']) {
                        $('#nbresuse-display').addClass('nbresuse-warn');
                    } else {
                        $('#nbresuse-display').removeClass('nbresuse-warn');
                    }
                }

                $('#nbresuse-mem').text(display);
            }
        });
    };

    function fillSizeList() {
        var sizes = null;
        $.getJSON({
            url: '/hub/migrate/sizes',
            success: function(data) {
                sizes = data; 
                var size_list = $('#size-list');
                sizes.forEach(function(size) {
                    size_list.append(
                        $('<li>').append(
                            $('<a>')
                                .attr('href', '/hub/migrate?migrate_to=' + size['slug'] + '&checkpoint=true')
                                .html(size['description'])
                                .click(function() {
                                    $('#save-notebook')
                                        .trigger('click');
                                    return true;
                                })
                        )
                    );
                });
            }
        });    
    }

    var load_ipython_extension = function () {
        setupDOM();
        fillSizeList();
        displayMetrics();
        // Update every five seconds, eh?
        setInterval(displayMetrics, 1000 * 5);

        document.addEventListener("visibilitychange", function () {
            // Update instantly when user activates notebook tab
            // FIXME: Turn off update timer completely when tab not in focus
            if (!document.hidden) {
                displayMetrics();
            }
        }, false);
    };

    return {
        load_ipython_extension: load_ipython_extension,
    };
});
