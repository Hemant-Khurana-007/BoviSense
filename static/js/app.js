const { createApp } = Vue;

createApp({
  data() {
    return {
      cows: [], page: 'dashboard', search: '', selectedFilter: 'All cows', selectedCow: null, navOpen: false, loadError: '',
      filters: ['All cows', 'Healthy', 'Needs attention'],
    };
  },
  computed: {
    totalCows() { return this.cows.length; },
    healthyCount() { return this.cows.filter(cow => cow.health === 'Healthy').length; },
    attentionCount() { return this.cows.filter(cow => cow.health !== 'Healthy').length; },
    healthyPercent() { return this.totalCows ? Math.round((this.healthyCount / this.totalCows) * 100) : 0; },
    filteredCows() {
      const term = this.search.trim().toLowerCase();
      return this.cows.filter(cow => {
        const matchesSearch = !term || `${cow.name} ${cow.id} ${cow.tag} ${cow.breed}`.toLowerCase().includes(term);
        const matchesFilter = this.selectedFilter === 'All cows' || (this.selectedFilter === 'Healthy' ? cow.health === 'Healthy' : cow.health !== 'Healthy');
        return matchesSearch && matchesFilter;
      });
    },
  },
  methods: {
    goTo(page, attentionOnly = false) {
      this.page = page;
      this.navOpen = false;
      this.selectedFilter = attentionOnly ? 'Needs attention' : 'All cows';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    selectCow(cow) { this.selectedCow = cow; },
    healthClass(health) { return health === 'Healthy' ? 'healthy' : health === 'Attention' ? 'attention' : 'observation'; },
    readableParameters(parameters) {
      const labels = { activity_level: 'Activity level', body_temp: 'Body temperature', udder_temp: 'Udder temperature', teat1_tds: 'Teat 1 TDS', teat2_tds: 'Teat 2 TDS', teat3_tds: 'Teat 3 TDS', teat4_tds: 'Teat 4 TDS' };
      return Object.fromEntries(Object.entries(parameters).filter(([key]) => key !== 'gps_coordinates').map(([key, value]) => [labels[key], value]));
    },
  },
  async mounted() {
    try {
      const response = await fetch('/api/cows');
      const payload = await response.json();
      if (!response.ok || !Array.isArray(payload)) throw new Error(payload.error || 'Unable to load herd data.');
      this.cows = payload;
    } catch (error) {
      this.cows = [];
      this.loadError = error.message || 'Unable to load herd data.';
    }
  },
}).mount('#app');
