<template>
<div>
  <instance-table
    fetch-instances-action-name="objectives/fetchFilteredObjectives"
    type="objective"
    :instances="objectives"
    base-url="/objectives"
    export-object-label="Objectives"
    column-data-resource="objectives"
    :server-items-length="total"
    />
</div>
</template>

<script>
import InstanceTable from './InstanceTable'
import { mapGetters } from 'vuex'

export default {
  components: {
    InstanceTable
  },
  computed: {
    ...mapGetters({
      objectives: 'objectives/objectives',
      total: 'objectives/total'
    })
  }
}
</script>
