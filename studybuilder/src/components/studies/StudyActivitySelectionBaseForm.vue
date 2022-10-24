<template>
<simple-form-dialog
  ref="form"
  :title="$t('StudyActivityBatchEditForm.title')"
  :help-items="helpItems"
  @close="close"
  @submit="$emit('submit')"
  :open="open"
  >
  <template v-slot:body>
    <p>{{ $t('StudyActivityBatchEditForm.note') }}</p>
    <div class="d-flex align-center">
      <div>{{ $t('StudyActivityBatchEditForm.items_selected') }} <span class="font-weight-bold">{{ selection.length }}</span></div>
      <div class="ml-10 d-flex align-center">
        {{ $t('StudyActivityBatchEditForm.show_items') }}
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
    <slot name="body"></slot>
  </template>
</simple-form-dialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'

export default {
  components: {
    SimpleFormDialog
  },
  props: {
    helpItems: Array,
    selection: Array,
    withDeleteAction: {
      type: Boolean,
      default: false
    },
    open: Boolean
  },
  data () {
    return {
      showItems: false
    }
  },
  methods: {
    close () {
      this.showItems = false
      this.$emit('close')
    },
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
