import { defineStore } from 'pinia'
import { getCities } from '@/api/cities'

const CITY_STORAGE_KEY = 'current_city'

function readStoredCity() {
  try {
    return uni.getStorageSync(CITY_STORAGE_KEY) || null
  } catch {
    return null
  }
}

function writeStoredCity(city) {
  try {
    if (city) {
      uni.setStorageSync(CITY_STORAGE_KEY, city)
    } else {
      uni.removeStorageSync(CITY_STORAGE_KEY)
    }
  } catch {
    // Storage failures should not block city selection.
  }
}

export const useCityStore = defineStore('city', {
  state: () => ({
    currentCity: readStoredCity(),
    cities: [],
    initialized: false,
  }),

  getters: {
    currentCityName: (state) => state.currentCity?.name || '选择城市',
  },

  actions: {
    async fetchCities() {
      try {
        const data = await getCities()
        this.cities = Array.isArray(data) ? data : []
        return this.cities
      } catch {
        this.cities = []
        return []
      }
    },

    async initCity() {
      const storedCity = readStoredCity()
      if (storedCity) {
        this.currentCity = storedCity
      }

      const cities = await this.fetchCities()
      if (cities.length === 0) {
        this.initialized = true
        return this.currentCity
      }

      const matchedStoredCity = this.currentCity
        ? cities.find(city => city.id === this.currentCity.id)
        : null
      const defaultCity = matchedStoredCity || cities[0]
      this.setCity(defaultCity)
      this.initialized = true
      return this.currentCity
    },

    setCity(city) {
      this.currentCity = city || null
      writeStoredCity(this.currentCity)
    },
  },
})
