import { createRouter, createWebHistory } from 'vue-router';
import PlayersView from './views/PlayersView.vue';
import PlayerFormView from './views/PlayerFormView.vue';
import PlayerDetailView from './views/PlayerDetailView.vue';
import StatsView from './views/StatsView.vue';
import GamesView from './views/GamesView.vue';
import GameDetailView from './views/GameDetailView.vue';
import AbilitiesView from './views/AbilitiesView.vue';
import RecordFormView from './views/RecordFormView.vue';
import ScheduleView from './views/ScheduleView.vue';
import EventsView from './views/EventsView.vue';
import SettingsView from './views/SettingsView.vue';

export const screens = [
  ['players', 'players', PlayersView, '選手一覧'],
  ['register', 'register_player', PlayerFormView, '選手登録'],
  ['edit', 'edit_player/:playerId(\\d+)', PlayerFormView, '選手情報編集'],
  ['detail', 'player_detail_R1/:playerId(\\d+)', PlayerDetailView, '選手詳細'],
  ['current', 'current_year_stats/:playerId(\\d+)', StatsView, '今年度個人成績'],
  ['history', 'player_history/:playerId(\\d+)', StatsView, '過去成績'],
  ['record', 'input_form_R1/:playerId(\\d+)', RecordFormView, '成績入力'],
  ['games', 'games', GamesView, '試合結果一覧'],
  ['game', 'game/:gameId', GameDetailView, '試合詳細'],
  ['teamstats', 'teamstats', StatsView, 'チーム成績'],
  ['annual', 'annual_stats_detail', StatsView, '個人成績'],
  ['pitchers', 'pitchers', StatsView, '投手成績'],
  ['abilities', 'pawapuro', AbilitiesView, '選手能力一覧'],
  ['meeting', 'record_summary', StatsView, '記録会成績'],
  ['schedule', 'schedule', ScheduleView, 'スケジュール'],
  ['events', 'events', EventsView, 'イベント'],
  ['regulation', 'admin/regulation', SettingsView, '規定打席'],
  ['qualitative', 'admin/qualitative_abilities', SettingsView, '特殊能力設定'],
];

export default createRouter({
  history: createWebHistory(),
  routes: [
    ...screens.map(([name, path, component, title]) => ({
      name, path: '/t/:teamSlug/' + path, component, meta: { title },
    })),
    { path: '/t/:teamSlug', redirect: to => `/t/${to.params.teamSlug}/players` },
    { path: '/t/:teamSlug/csv_data', redirect: to => `/t/${to.params.teamSlug}/players` },
    { path: '/:pathMatch(.*)*', component: { template: '<p>画面が見つかりません。</p>' }, meta: { notFound: true } },
  ],
  scrollBehavior(to, from, saved) { return saved || (to.path === from.path ? {} : { top: 0 }); },
});
