(function () {
    function ready(callback) {
        if (document.readyState !== 'loading') {
            callback();
        } else {
            document.addEventListener('DOMContentLoaded', callback);
        }
    }

    function showToast(title, message) {
        var stack = document.querySelector('.fas-toast-stack');
        if (!stack) {
            stack = document.createElement('div');
            stack.className = 'fas-toast-stack';
            document.body.appendChild(stack);
        }

        var toast = document.createElement('div');
        toast.className = 'fas-toast';

        var heading = document.createElement('strong');
        heading.textContent = title;
        var text = document.createElement('span');
        text.textContent = message;

        toast.appendChild(heading);
        toast.appendChild(text);
        stack.appendChild(toast);

        window.setTimeout(function () {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-8px)';
            window.setTimeout(function () {
                toast.remove();
            }, 220);
        }, 5200);
    }

    function normaliseText(value) {
        return (value || '')
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function inferRole() {
        var pageText = normaliseText(document.body.textContent);
        var links = Array.prototype.slice.call(document.querySelectorAll('a[href]')).map(function (link) {
            return link.getAttribute('href') || '';
        }).join(' ');

        if (links.indexOf('dashboard_jugador') !== -1 || links.indexOf('editar_jugador_perfil') !== -1) {
            return { label: 'Jugador', icon: 'fa-user' };
        }
        if (links.indexOf('dashboard_entrenador') !== -1 || links.indexOf('/entrenamientos/lista/') !== -1) {
            return { label: 'Entrenador', icon: 'fa-clipboard-list' };
        }
        if (links.indexOf('dashboard_admin') !== -1 || links.indexOf('/admin/') !== -1) {
            return { label: 'Administrador', icon: 'fa-shield-halved' };
        }
        return { label: 'Usuario', icon: 'fa-user-check' };
    }

    function findTopActionContainer() {
        return document.querySelector('.navbar .navbar-nav.ms-auto') ||
            document.querySelector('.navbar .ms-auto.d-flex') ||
            document.querySelector('.navbar .ms-auto') ||
            document.querySelector('nav.bg-fas-blue .flex.items-center.gap-4') ||
            document.querySelector('nav.bg-fas-blue .flex.items-center.justify-between > .flex:last-child');
    }

    function findProfileLink() {
        return document.querySelector('a[href*="perfil/editar"], a[href*="perfil/jugador/editar"], a[href*="editar_perfil"], a[href*="editar_jugador_perfil"]');
    }

    function wrapForTopbar(container, node) {
        if (!container || container.tagName !== 'UL') return node;
        var item = document.createElement('li');
        item.className = 'nav-item d-flex align-items-center';
        item.appendChild(node);
        return item;
    }

    function collectPageSignals() {
        var cards = document.querySelectorAll('.card, .fas-home-card').length;
        var rows = Array.prototype.slice.call(document.querySelectorAll('tbody tr')).filter(function (row) {
            return row.offsetParent !== null && !row.classList.contains('fas-empty-row');
        }).length;
        var pending = Array.prototype.slice.call(document.querySelectorAll('.badge, .alert, td, span')).filter(function (node) {
            var text = normaliseText(node.textContent);
            return text.indexOf('pendiente') !== -1 || text.indexOf('sin marcar') !== -1 || text.indexOf('programado') !== -1;
        }).length;

        return { cards: cards, rows: rows, pending: pending };
    }

    function buildNotifications(role) {
        var signals = collectPageSignals();
        var title = document.querySelector('h1, h2, h3');
        var pageName = title ? title.textContent.replace(/\s+/g, ' ').trim() : 'esta vista';
        var items = [];

        if (signals.pending > 0) {
            items.push({
                icon: 'fa-circle-info',
                title: signals.pending + ' elemento(s) por revisar',
                body: 'Hay estados pendientes, programados o sin marcar en ' + pageName + '.'
            });
        }

        if (signals.rows > 0) {
            items.push({
                icon: 'fa-table-list',
                title: signals.rows + ' registro(s) visibles',
                body: 'Puedes usar el buscador de la tabla para encontrar informacion rapido.'
            });
        }

        if (role.label === 'Jugador') {
            items.push({ icon: 'fa-futbol', title: 'Mantente atento', body: 'Revisa entrenamientos y torneos para no perder novedades.' });
        } else if (role.label === 'Entrenador') {
            items.push({ icon: 'fa-chart-line', title: 'Gestion deportiva', body: 'Revisa asistencia, reportes y estadisticas antes de cerrar la jornada.' });
        } else if (role.label === 'Administrador') {
            items.push({ icon: 'fa-sitemap', title: 'Panel administrativo', body: 'Equipos, torneos y canchas quedan mejor cuando los estados estan al dia.' });
        } else {
            items.push({ icon: 'fa-lightbulb', title: 'Consejo rapido', body: 'Mantener tu perfil actualizado mejora las notificaciones.' });
        }

        return items.slice(0, 4);
    }

    function addTopbarExperience() {
        var container = findTopActionContainer();
        if (!container) return;

        var role = inferRole();
        var profileLink = findProfileLink();

        var notifications = buildNotifications(role);
        var notifyWrap = document.createElement('div');
        notifyWrap.className = 'fas-notify-wrap';
        notifyWrap.innerHTML = '<button type="button" class="fas-notify-button" aria-label="Notificaciones"><i class="fas fa-bell"></i><span class="fas-notify-count">' + notifications.length + '</span></button>';

        var panel = document.createElement('div');
        panel.className = 'fas-notify-panel';
        panel.hidden = true;
        panel.innerHTML = '<div class="fas-notify-head"><strong>Notificaciones</strong><span class="badge bg-warning text-dark">Hoy</span></div>';

        var list = document.createElement('div');
        list.className = 'fas-notify-list';
        notifications.forEach(function (item) {
            var row = document.createElement('div');
            row.className = 'fas-notify-item';
            row.innerHTML = '<i class="fas ' + item.icon + '"></i><span>' + item.title + '<small>' + item.body + '</small></span>';
            list.appendChild(row);
        });
        panel.appendChild(list);
        notifyWrap.appendChild(panel);

        notifyWrap.querySelector('button').addEventListener('click', function (event) {
            event.stopPropagation();
            panel.hidden = !panel.hidden;
        });
        document.addEventListener('click', function () {
            panel.hidden = true;
        });

        var notifyNode = wrapForTopbar(container, notifyWrap);

        if (profileLink && profileLink.parentElement && profileLink.parentElement.classList.contains('nav-item')) {
            container.insertBefore(notifyNode, profileLink.parentElement);
        } else if (profileLink) {
            container.insertBefore(notifyNode, profileLink);
        } else {
            container.insertBefore(notifyNode, container.firstChild);
        }
    }

    function enhanceAlerts() {
        document.querySelectorAll('.alert').forEach(function (alert) {
            var message = alert.textContent.replace(/\s+/g, ' ').trim();
            if (!message) return;
            var title = alert.classList.contains('alert-danger') ? 'Atencion requerida' : 'Notificacion';
            showToast(title, message.slice(0, 170));
        });
    }

    function removeOldTechnicalPanels() {
        document.querySelectorAll('.fas-match-board, .fas-visual-strip').forEach(function (node) {
            node.remove();
        });
    }

    function enhanceTables() {
        document.querySelectorAll('.table').forEach(function (table) {
            if (table.dataset.fasEnhanced === 'true') return;
            table.dataset.fasEnhanced = 'true';

            var headers = Array.prototype.slice.call(table.querySelectorAll('thead th')).map(function (header) {
                return header.textContent.replace(/\s+/g, ' ').trim();
            });
            table.querySelectorAll('tbody tr').forEach(function (row) {
                Array.prototype.slice.call(row.children).forEach(function (cell, index) {
                    if (!cell.dataset.fasLabel && headers[index]) {
                        cell.dataset.fasLabel = headers[index];
                    }
                });
            });

            var rows = Array.prototype.slice.call(table.querySelectorAll('tbody tr'));
            if (rows.length < 4) return;

            var wrapper = table.closest('.table-responsive') || table.parentElement;
            if (!wrapper || !wrapper.parentElement) return;

            var toolbar = document.createElement('div');
            toolbar.className = 'fas-toolbar d-flex flex-column flex-md-row align-items-md-center gap-2';

            var input = document.createElement('input');
            input.type = 'search';
            input.className = 'form-control';
            input.placeholder = 'Buscar por nombre, fecha o estado...';
            input.setAttribute('aria-label', 'Buscar en tabla');

            var counter = document.createElement('span');
            counter.className = 'badge bg-light text-dark';
            counter.textContent = rows.length + ' resultados';

            toolbar.appendChild(input);
            toolbar.appendChild(counter);
            wrapper.parentElement.insertBefore(toolbar, wrapper);

            var emptyRow = document.createElement('tr');
            var emptyCell = document.createElement('td');
            emptyCell.className = 'fas-empty-row';
            emptyCell.colSpan = Math.max(1, table.querySelectorAll('thead th').length);
            emptyCell.textContent = 'No encontramos resultados con esa busqueda.';
            emptyRow.appendChild(emptyCell);
            emptyRow.hidden = true;
            table.querySelector('tbody').appendChild(emptyRow);

            input.addEventListener('input', function () {
                var query = input.value.toLowerCase().trim();
                var visible = 0;
                rows.forEach(function (row) {
                    var match = row.textContent.toLowerCase().indexOf(query) !== -1;
                    row.hidden = !match;
                    if (match) visible += 1;
                });
                emptyRow.hidden = visible !== 0;
                counter.textContent = visible + ' de ' + rows.length;
            });
        });
    }

    function enhanceCards() {
        document.querySelectorAll('.card, .fas-home-card, .fas-note-card').forEach(function (card, index) {
            card.classList.add('fas-reveal');
            card.style.animationDelay = Math.min(index * 30, 240) + 'ms';
        });
    }

    function addFriendlyTip() {
        if (document.querySelector('.fas-welcome-panel') || document.body.dataset.fasTipShown === 'true') return;

        var target = document.querySelector('main.col-md-9, main.col-lg-10, .col-12.col-md-9.col-lg-10, main');
        if (!target) return;

        var titleNode = target.querySelector('h1, h2');
        if (!titleNode) return;

        var tips = [
            'Revisa primero lo mas urgente y luego avanza con calma.',
            'Un perfil actualizado ayuda a que tu equipo te encuentre facil.',
            'Si algo no aparece, prueba actualizar la pagina o revisa tu menu lateral.',
            'Cada entrenamiento cuenta. Pequenos avances tambien suman.'
        ];

        var note = document.createElement('div');
        note.className = 'fas-soft-note fas-reveal';
        note.innerHTML = '<i class="fas fa-lightbulb"></i><span>' + tips[Math.floor(Math.random() * tips.length)] + '</span>';

        titleNode.insertAdjacentElement('afterend', note);
        document.body.dataset.fasTipShown = 'true';
    }

    function addFloatingActions() {
        if (document.querySelector('.fas-top-actions')) return;

        var actions = document.createElement('div');
        actions.className = 'fas-top-actions';

        var theme = document.createElement('button');
        theme.type = 'button';
        theme.className = 'fas-fab fas-theme-toggle';
        theme.title = 'Cambiar contraste';
        theme.setAttribute('aria-label', 'Cambiar entre modo claro y oscuro');
        theme.appendChild(document.createElement('i')).className = 'fas fa-moon';
        theme.addEventListener('click', function () {
            var nextTheme = document.documentElement.dataset.fasTheme === 'dark' ? 'light' : 'dark';
            setTheme(nextTheme, true);
        });

        var notify = document.createElement('button');
        notify.type = 'button';
        notify.className = 'fas-fab';
        notify.title = 'Consejo';
        notify.appendChild(document.createElement('i')).className = 'fas fa-bell';
        notify.addEventListener('click', function () {
            showToast('Mensaje para hoy', 'Haz una cosa a la vez. El sistema esta para ayudarte, no para complicarte.');
        });

        var top = document.createElement('button');
        top.type = 'button';
        top.className = 'fas-fab';
        top.title = 'Volver arriba';
        top.appendChild(document.createElement('i')).className = 'fas fa-arrow-up';
        top.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });

        actions.appendChild(theme);
        actions.appendChild(notify);
        actions.appendChild(top);
        document.body.appendChild(actions);
    }

    function setTheme(theme, persist) {
        var selected = theme === 'dark' ? 'dark' : 'light';
        document.documentElement.dataset.fasTheme = selected;
        if (persist) {
            try {
                window.localStorage.setItem('fas-theme', selected);
            } catch (error) {}
        }

        document.querySelectorAll('.fas-theme-toggle i').forEach(function (icon) {
            icon.className = selected === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        });
        document.querySelectorAll('.fas-theme-toggle').forEach(function (button) {
            button.title = selected === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';
        });
    }

    function initTheme() {
        var stored = null;
        try {
            stored = window.localStorage.getItem('fas-theme');
        } catch (error) {}

        if (stored === 'dark' || stored === 'light') {
            setTheme(stored, false);
            return;
        }

        setTheme('light', false);
    }

    function polishStatusBadges() {
        var map = [
            ['programado', 'fas-state-programado'],
            ['confirmado', 'fas-state-confirmado'],
            ['aprobado', 'fas-state-aprobado'],
            ['en curso', 'fas-state-en-curso'],
            ['activo', 'fas-state-activo'],
            ['asistio', 'fas-state-asistio'],
            ['finalizado', 'fas-state-finalizado'],
            ['sin marcar', 'fas-state-sin-marcar'],
            ['pendiente', 'fas-state-pendiente'],
            ['rechazado', 'fas-state-rechazado'],
            ['cancelado', 'fas-state-cancelado'],
            ['falto', 'fas-state-falto']
        ];

        document.querySelectorAll('.badge').forEach(function (badge) {
            var text = normaliseText(badge.textContent);
            map.forEach(function (entry) {
                if (text.indexOf(entry[0]) !== -1) {
                    badge.classList.add(entry[1]);
                }
            });
        });
    }

    function polishEmptyStates() {
        document.querySelectorAll('td, .card-body, main, .container').forEach(function (node) {
            if (node.dataset.fasEmptyPolished === 'true') return;
            var text = normaliseText(node.textContent);
            var isEmpty = text.length < 180 && (
                text.indexOf('no hay') !== -1 ||
                text.indexOf('no tienes') !== -1 ||
                text.indexOf('sin registros') !== -1 ||
                text.indexOf('sin equipos') !== -1 ||
                text.indexOf('todavia') !== -1
            );
            if (!isEmpty) return;
            node.dataset.fasEmptyPolished = 'true';
            node.classList.add('fas-polished-empty');
            if (!node.querySelector('.fas-empty-icon')) {
                var icon = document.createElement('div');
                icon.className = 'fas-empty-icon';
                icon.innerHTML = '<i class="fas fa-clipboard-list"></i>';
                node.insertBefore(icon, node.firstChild);
            }
        });
    }

    function highlightImportantRows() {
        document.querySelectorAll('tbody tr').forEach(function (row) {
            var text = normaliseText(row.textContent);
            if (text.indexOf('pendiente') !== -1 || text.indexOf('programado') !== -1 || text.indexOf('sin marcar') !== -1) {
                row.classList.add('fas-row-highlight');
            }
        });
    }

    function confirmDangerForms() {
        document.querySelectorAll('form').forEach(function (form) {
            if (form.dataset.fasConfirm === 'true') return;
            var action = (form.getAttribute('action') || '').toLowerCase();
            var button = form.querySelector('.btn-danger, button[type="submit"].btn-danger');
            if (!button || action.indexOf('eliminar') === -1) return;
            form.dataset.fasConfirm = 'true';
            form.addEventListener('submit', function (event) {
                if (!window.confirm('Confirma que deseas realizar esta accion.')) {
                    event.preventDefault();
                }
            });
        });
    }

    ready(function () {
        initTheme();
        removeOldTechnicalPanels();
        enhanceAlerts();
        enhanceTables();
        enhanceCards();
        addFriendlyTip();
        addTopbarExperience();
        polishStatusBadges();
        polishEmptyStates();
        highlightImportantRows();
        // addFloatingActions();
        confirmDangerForms();
    });
})();
