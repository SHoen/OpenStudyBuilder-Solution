<template>
<div>
  <div class="d-flex align-center">
    <div>{{ title }} <span class="font-weight-bold">{{ selection.length }}</span></div>
    <div class="ml-10 d-flex align-center">
      {{ $t('StudyActivitySelectionTable.show_items') }}
      <v-checkbox
        v-model="showItems"
        on-icon="mdi-close-circle"
        off-icon="mdi-dots-horizontal-circle"
        hide-details
        class="ml-2"
        />
    </div>
  </div>
  <v-simple-table v-if="showItems" dense class="mt-4 preview">
    <template v-slot:default>
      <tbody>
        <tr
          v-for="item in selection"
          :key="item.name"
          >
          <td>{{ item.activity.name }}</td>
          <td v-if="withDeleteAction" class="text-right">
            <v-btn
              color="error"
              icon
              @click="removeItem(item)"
              >
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </td>
        </tr>
      </tbody>
    </template>
  </v-simple-table>
</div>
</template>

<script>
export default {
  props: {
    selection: Array,
    title: String,
    withDeleteAction: {
      type: Boolean,
      default: true
    }
  },
  data () {
    return {
      showItems: false
    }
  },
  methods: {
    removeItem (item) {
      this.$emit('remove', item)
    }
  }
}
</script>

<style scoped lang="scss">
.preview {
  max-height: 150px;
  overflow: auto;
}
</style>
