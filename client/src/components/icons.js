export const screenIcons = {players:'users',register:'user-plus',edit:'edit',detail:'user',current:'chart',history:'history',record:'clipboard',games:'ball',game:'ball',teamstats:'chart',annual:'trophy',pitchers:'ball',abilities:'sparkles',meeting:'clipboard',schedule:'calendar',events:'users',regulation:'settings',qualitative:'sparkles'};
export function iconForPath(path) {
  return ({players:'users',register_player:'user-plus',edit_player:'edit',player_detail_R1:'user',current_year_stats:'chart',player_history:'history',input_form_R1:'clipboard',games:'ball',game:'ball',teamstats:'chart',annual_stats_detail:'trophy',pitchers:'ball',pawapuro:'sparkles',record_summary:'clipboard',schedule:'calendar',events:'users'})[String(path).split('/')[0]] || 'settings';
}
