<template>
<n-n-table
  @filter="fetchData"
  :headers="headers"
  item-key="uid"
  :server-items-length="total"
  :options.sync="options"
  :items="items">
</n-n-table>
</template>

<script>
import NNTable from '@/components/tools/NNTable'
import { mapGetters } from 'vuex'
import listings from '@/api/listings'

export default {
  components: {
    NNTable
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  props: {
    type: {
      type: String,
      default: 'TA'
    }
  },
  data () {
    return {
      headers: [],
      taHeaders: [
        { text: this.$t('SdtmDesignTable.study_id'), value: 'STUDYID' },
        { text: this.$t('SdtmDesignTable.domain_abbr'), value: 'DOMAIN' },
        { text: this.$t('SdtmDesignTable.planned_arm'), value: 'ARMCD' },
        { text: this.$t('SdtmDesignTable.arm_desc'), value: 'ARM' },
        { text: this.$t('SdtmDesignTable.planned_order_of_elem'), value: 'TAETORD' },
        { text: this.$t('SdtmDesignTable.elem_code'), value: 'ETCD' },
        { text: this.$t('SdtmDesignTable.elem_desc'), value: 'ELEMENT' },
        { text: this.$t('SdtmDesignTable.branch'), value: 'TABRANCH' },
        { text: this.$t('SdtmDesignTable.transition_rule'), value: 'TATRANS' },
        { text: this.$t('SdtmDesignTable.epoch'), value: 'EPOCH' }
      ],
      tvHeaders: [
        { text: this.$t('SdtmDesignTable.study_id'), value: 'STUDYID' },
        { text: this.$t('SdtmDesignTable.domain_abbr'), value: 'DOMAIN' },
        { text: this.$t('SdtmDesignTable.visit_number'), value: 'VISITNUM' },
        { text: this.$t('SdtmDesignTable.visit_name'), value: 'VISIT' },
        { text: this.$t('SdtmDesignTable.planned_study_day'), value: 'VISITDY' },
        { text: this.$t('SdtmDesignTable.planned_arm_code'), value: 'ARMCD' },
        { text: this.$t('SdtmDesignTable.planned_arm_desc'), value: 'ARM' },
        { text: this.$t('SdtmDesignTable.visit_start_rule'), value: 'TVSTRL' },
        { text: this.$t('SdtmDesignTable.visit_end_rule'), value: 'TVENRL' }
      ],
      teHeaders: [
        { text: this.$t('SdtmDesignTable.study_id'), value: 'STUDYID' },
        { text: this.$t('SdtmDesignTable.domain_abbr'), value: 'DOMAIN' },
        { text: this.$t('SdtmDesignTable.elem_code'), value: 'ETCD' },
        { text: this.$t('SdtmDesignTable.elem_desc'), value: 'ELEMENT' },
        { text: this.$t('SdtmDesignTable.elem_start_rule'), value: 'TESTRL' },
        { text: this.$t('SdtmDesignTable.elem_end_rule'), value: 'TEENRL' },
        { text: this.$t('SdtmDesignTable.elem_planned_duration'), value: 'TEDUR' }
      ],
      tiHeaders: [
        { text: this.$t('SdtmDesignTable.study_id'), value: 'STUDYID' },
        { text: this.$t('SdtmDesignTable.domain_abbr'), value: 'DOMAIN' },
        { text: this.$t('SdtmDesignTable.incl_excl_short_name'), value: 'IETESTCD' },
        { text: this.$t('SdtmDesignTable.incl_excl_criterion'), value: 'IETEST' },
        { text: this.$t('SdtmDesignTable.incl_excl_cat'), value: 'IECAT' },
        { text: this.$t('SdtmDesignTable.incl_excl_subcat'), value: 'IESCAT' },
        { text: this.$t('SdtmDesignTable.incl_excl_criterion_rule'), value: 'TIRL' },
        { text: this.$t('SdtmDesignTable.protocol_criteria_versions'), value: 'TIVERS' }
      ],
      tsHeaders: [
        { text: this.$t('SdtmDesignTable.study_id'), value: 'STUDYID' },
        { text: this.$t('SdtmDesignTable.domain_abbr'), value: 'DOMAIN' },
        { text: this.$t('SdtmDesignTable.sequence_number'), value: 'TSSEQ' },
        { text: this.$t('SdtmDesignTable.group_id'), value: 'TSGRPID' },
        { text: this.$t('SdtmDesignTable.trial_summary_short_name'), value: 'TSPARMCD' },
        { text: this.$t('SdtmDesignTable.trial_summary_param'), value: 'TSPARM' },
        { text: this.$t('SdtmDesignTable.param_value'), value: 'TSVAL' },
        { text: this.$t('SdtmDesignTable.param_null'), value: 'TSVALNF' },
        { text: this.$t('SdtmDesignTable.param_value_code'), value: 'TSVALCD' },
        { text: this.$t('SdtmDesignTable.reference_term_name'), value: 'TSVCDREF' },
        { text: this.$t('SdtmDesignTable.reference_term_version'), value: 'TSVCDVER' }
      ],
      items: [],
      options: {},
      total: 0
    }
  },
  methods: {
    fetchData () {
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true
      }
      listings.getAllSdtm(this.selectedStudy.uid, params, this.type).then(resp => {
        this.items = resp.data.items
        this.total = resp.data.total
      })
    }
  },
  mounted () {
    if (this.type === 'TA') {
      this.headers = this.taHeaders
    } else if (this.type === 'TV') {
      this.headers = this.tvHeaders
    } else if (this.type === 'TE') {
      this.headers = this.teHeaders
    } else if (this.type === 'TI') {
      this.headers = this.tiHeaders
    } else if (this.type === 'TS') {
      this.headers = this.tsHeaders
    }
  },
  watch: {
    options () {
      this.fetchData()
    },
    type () {
      if (this.type === 'TA') {
        this.headers = this.taHeaders
      } else if (this.type === 'TV') {
        this.headers = this.tvHeaders
      } else if (this.type === 'TE') {
        this.headers = this.teHeaders
      } else if (this.type === 'TI') {
        this.headers = this.tiHeaders
      } else if (this.type === 'TS') {
        this.headers = this.tsHeaders
      }
    }
  }
}
</script>
